#!/usr/bin/env python3
"""Durable review reservations, not an agent launcher or acceptance gate.

Rounds count successful reservations, not external calls. This tool cannot
dispatch reviewers, enforce budget or elapsed time, or certify a product.
"""

import argparse
import json
import math
import os
import sqlite3
import sys
import tempfile
import uuid
from datetime import datetime, timezone


class GuardError(Exception):
    pass


class JsonParser(argparse.ArgumentParser):
    def error(self, message):
        raise GuardError(message)


SCHEMA = """
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE outcomes (id TEXT PRIMARY KEY, rounds INTEGER NOT NULL DEFAULT 0 CHECK(rounds >= 0));
CREATE TABLE outcome_phases (outcome_id TEXT NOT NULL REFERENCES outcomes(id), kind TEXT NOT NULL CHECK(kind IN ('plan', 'product')), rounds INTEGER NOT NULL DEFAULT 0 CHECK(rounds >= 0), PRIMARY KEY (outcome_id, kind));
CREATE TABLE registrations (outcome_id TEXT PRIMARY KEY REFERENCES outcomes(id), reason TEXT NOT NULL, registered_at TEXT NOT NULL);
CREATE TABLE tickets (ticket TEXT PRIMARY KEY, outcome_key TEXT NOT NULL);
CREATE TABLE reservations (id INTEGER PRIMARY KEY, ticket TEXT NOT NULL, kind TEXT NOT NULL CHECK(kind IN ('plan', 'product')), criteria TEXT NOT NULL, purpose TEXT NOT NULL, expected TEXT NOT NULL, minutes REAL NOT NULL CHECK(minutes > 0), decision TEXT, changed_approach TEXT, exception TEXT, result TEXT CHECK(result IN ('pass', 'fail', 'incomplete', 'not-started')), evidence TEXT, created_at TEXT NOT NULL, finished_at TEXT);
CREATE TABLE reservation_outcomes (reservation_id INTEGER NOT NULL REFERENCES reservations(id), outcome_id TEXT NOT NULL REFERENCES outcomes(id), round INTEGER NOT NULL CHECK(round > 0), PRIMARY KEY (reservation_id, outcome_id));
CREATE INDEX reservation_outcome_lookup ON reservation_outcomes(outcome_id);
"""

V1_TABLES = {
    "meta": {"key", "value"}, "outcomes": {"id", "rounds"},
    "tickets": {"ticket", "outcome_key"},
    "reservations": {"id", "ticket", "criteria", "purpose", "expected", "minutes", "decision", "changed_approach", "exception", "result", "evidence", "created_at", "finished_at"},
    "reservation_outcomes": {"reservation_id", "outcome_id", "round"},
}


def emit(payload, code=0):
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return code


def now():
    return datetime.now(timezone.utc).isoformat()


def nonblank(value, name):
    value = (value or "").strip()
    if not value:
        raise GuardError("%s must be nonblank" % name)
    return value


def ids(values, name="outcomes"):
    result = [nonblank(value, name) for value in values]
    if len(set(result)) != len(result):
        raise GuardError("%s must be unique" % name)
    return result


def minute_value(value):
    try:
        minutes = float(value)
    except (TypeError, ValueError):
        raise GuardError("minutes must be a positive finite number")
    if not math.isfinite(minutes) or minutes <= 0:
        raise GuardError("minutes must be a positive finite number")
    return minutes


def close(con):
    if con is not None:
        try:
            con.close()
        except sqlite3.Error:
            pass


def rollback(con):
    try:
        con.rollback()
    except sqlite3.Error:
        pass


def schema_version(con):
    try:
        row = con.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()
    except sqlite3.Error as error:
        raise GuardError("database schema is invalid: %s" % error)
    return row[0] if row else None


def connect(path, required_version="2"):
    if not os.path.isfile(path):
        raise GuardError("database is missing or is not a regular file")
    con = None
    try:
        con = sqlite3.connect(path, timeout=0.25, isolation_level=None)
        con.execute("PRAGMA busy_timeout = 250")
        con.execute("PRAGMA foreign_keys = ON")
        version = schema_version(con)
        if version != required_version:
            if version == "1":
                raise GuardError("database schema is v1; run migrate explicitly")
            raise GuardError("database schema is unsupported or malformed")
        return con
    except GuardError:
        close(con); raise
    except sqlite3.Error as error:
        close(con); raise GuardError("database is unavailable: %s" % error)


def create_schema(con, outcome_ids, reason, registered_at):
    con.executescript(SCHEMA)
    con.execute("INSERT INTO meta(key, value) VALUES ('schema_version', '2')")
    con.executemany("INSERT INTO outcomes(id) VALUES (?)", [(item,) for item in outcome_ids])
    con.executemany("INSERT INTO outcome_phases(outcome_id, kind) VALUES (?, ?)", [(item, kind) for item in outcome_ids for kind in ("plan", "product")])
    con.executemany("INSERT INTO registrations(outcome_id, reason, registered_at) VALUES (?, ?, ?)", [(item, reason, registered_at) for item in outcome_ids])


def init(args):
    outcome_ids = ids(args.outcomes)
    target = os.path.abspath(args.database)
    parent, base = os.path.dirname(target), os.path.basename(target)
    if os.path.lexists(target):
        raise GuardError("refusing to overwrite existing database")
    temp = con = None
    try:
        fd, temp = tempfile.mkstemp(prefix=".%s.%s." % (base, uuid.uuid4().hex), suffix=".tmp", dir=parent)
        os.close(fd)
        con = sqlite3.connect(temp, timeout=0.25, isolation_level=None)
        con.execute("PRAGMA foreign_keys = ON")
        create_schema(con, outcome_ids, "initial registration", now())
        close(con); con = None
        # Atomic non-overwriting publication. Never replace a concurrent ledger.
        os.link(temp, target)
    except FileExistsError:
        raise GuardError("refusing to overwrite existing database")
    except (OSError, sqlite3.Error) as error:
        raise GuardError("could not initialize database: %s" % error)
    finally:
        close(con)
        if temp and os.path.lexists(temp):
            try:
                os.unlink(temp)
            except OSError:
                pass
    return {"ok": True, "outcomes": outcome_ids, "rounds_note": "rounds count reservations, not external calls"}


def reserve(args):
    outcome_ids, ticket = ids(args.outcomes), nonblank(args.ticket, "ticket")
    kind, criteria, purpose, expected = args.kind, nonblank(args.criteria, "criteria"), nonblank(args.purpose, "purpose"), nonblank(args.expected, "expected")
    minutes = minute_value(args.minutes)
    decision, changed, exception = (args.decision or "").strip(), (args.changed_approach or "").strip(), (args.exception or "").strip()
    con = connect(args.database)
    try:
        con.execute("BEGIN IMMEDIATE")
        found = {row[0]: row[1] for row in con.execute("SELECT id, rounds FROM outcomes WHERE id IN (%s)" % ",".join("?" * len(outcome_ids)), outcome_ids)}
        missing = [item for item in outcome_ids if item not in found]
        if missing: raise GuardError("unknown original outcome IDs: %s" % ",".join(missing))
        active = con.execute("SELECT DISTINCT ro.outcome_id FROM reservation_outcomes ro JOIN reservations r ON r.id = ro.reservation_id WHERE r.result IS NULL AND ro.outcome_id IN (%s)" % ",".join("?" * len(outcome_ids)), outcome_ids).fetchall()
        if active: raise GuardError("outcomes already have active reservations: %s" % ",".join(row[0] for row in active))
        key = json.dumps(sorted(outcome_ids), separators=(",", ":"))
        prior = con.execute("SELECT outcome_key FROM tickets WHERE ticket = ?", (ticket,)).fetchone()
        if prior and prior[0] != key: raise GuardError("ticket alias is already bound to different original outcomes")
        rows = con.execute("SELECT outcome_id, rounds FROM outcome_phases WHERE kind = ? AND outcome_id IN (%s)" % ",".join("?" * len(outcome_ids)), [kind, *outcome_ids]).fetchall()
        phase_counts = dict(rows)
        if len(phase_counts) != len(outcome_ids): raise GuardError("database phase history is malformed")
        phase_rounds = {item: phase_counts[item] + 1 for item in outcome_ids}
        highest = max(phase_rounds.values())
        if highest >= 3 and (not decision or not changed): raise GuardError("round 3 and later require nonblank decision and changed approach")
        if highest >= 4 and not exception: raise GuardError("round 4 and later require a nonblank exception")
        if not prior: con.execute("INSERT INTO tickets(ticket, outcome_key) VALUES (?, ?)", (ticket, key))
        reservation = con.execute("INSERT INTO reservations(ticket, kind, criteria, purpose, expected, minutes, decision, changed_approach, exception, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (ticket, kind, criteria, purpose, expected, minutes, decision or None, changed or None, exception or None, now())).lastrowid
        con.executemany("INSERT INTO reservation_outcomes(reservation_id, outcome_id, round) VALUES (?, ?, ?)", [(reservation, item, phase_rounds[item]) for item in outcome_ids])
        con.executemany("UPDATE outcome_phases SET rounds = rounds + 1 WHERE outcome_id = ? AND kind = ?", [(item, kind) for item in outcome_ids])
        con.executemany("UPDATE outcomes SET rounds = rounds + 1 WHERE id = ?", [(item,) for item in outcome_ids])
        con.commit()
    except (GuardError, sqlite3.Error) as error:
        rollback(con)
        if isinstance(error, GuardError): raise
        raise GuardError("reservation denied: %s" % error)
    finally:
        close(con)
    return {"ok": True, "reservation": reservation, "kind": kind, "outcomes": [{"id": item, "phase_round": phase_rounds[item], "total_round": found[item] + 1} for item in outcome_ids], "rounds_note": "rounds count reservations, not external calls"}


def add_outcomes(args):
    outcome_ids, reason = ids(args.outcomes), nonblank(args.reason, "reason")
    con = connect(args.database)
    try:
        con.execute("BEGIN IMMEDIATE")
        existing = [row[0] for row in con.execute("SELECT id FROM outcomes WHERE id IN (%s)" % ",".join("?" * len(outcome_ids)), outcome_ids)]
        if existing: raise GuardError("original outcome IDs already exist: %s" % ",".join(existing))
        stamp = now()
        con.executemany("INSERT INTO outcomes(id) VALUES (?)", [(item,) for item in outcome_ids])
        con.executemany("INSERT INTO outcome_phases(outcome_id, kind) VALUES (?, ?)", [(item, kind) for item in outcome_ids for kind in ("plan", "product")])
        con.executemany("INSERT INTO registrations(outcome_id, reason, registered_at) VALUES (?, ?, ?)", [(item, reason, stamp) for item in outcome_ids])
        con.commit()
    except (GuardError, sqlite3.Error) as error:
        rollback(con)
        if isinstance(error, GuardError): raise
        raise GuardError("add outcomes denied: %s" % error)
    finally:
        close(con)
    return {"ok": True, "outcomes": outcome_ids, "reason": reason}


def finish(args):
    try: reservation = int(args.reservation)
    except (TypeError, ValueError): raise GuardError("reservation must be an integer")
    if reservation <= 0: raise GuardError("reservation must be an integer")
    if args.result not in {"pass", "fail", "incomplete", "not-started"}: raise GuardError("result is invalid")
    evidence = nonblank(args.evidence, "evidence")
    con = connect(args.database)
    try:
        con.execute("BEGIN IMMEDIATE")
        row = con.execute("SELECT result FROM reservations WHERE id = ?", (reservation,)).fetchone()
        if row is None: raise GuardError("unknown reservation")
        if row[0] is not None: raise GuardError("reservation is already terminal")
        con.execute("UPDATE reservations SET result = ?, evidence = ?, finished_at = ? WHERE id = ?", (args.result, evidence, now(), reservation)); con.commit()
    except (GuardError, sqlite3.Error) as error:
        rollback(con)
        if isinstance(error, GuardError): raise
        raise GuardError("finish denied: %s" % error)
    finally:
        close(con)
    return {"ok": True, "reservation": reservation, "result": args.result, "rounds_note": "a not-started result does not reset reservation rounds"}


def elapsed(created_at):
    try:
        stamp = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        if stamp.tzinfo is None: raise ValueError()
    except (AttributeError, ValueError):
        raise GuardError("database contains malformed reservation timestamp")
    return max(0.0, (datetime.now(timezone.utc) - stamp.astimezone(timezone.utc)).total_seconds() / 60.0)


def status(args):
    con = connect(args.database)
    try:
        phases = {}
        for outcome_id, kind, rounds in con.execute("SELECT outcome_id, kind, rounds FROM outcome_phases ORDER BY outcome_id, kind"):
            phases.setdefault(outcome_id, {})[kind] = rounds
        outcomes = [{"id": item, "rounds": rounds, "phase_rounds": phases.get(item, {})} for item, rounds in con.execute("SELECT id, rounds FROM outcomes ORDER BY id")]
        active = []
        for row in con.execute("SELECT id, ticket, kind, criteria, purpose, expected, minutes, decision, changed_approach, exception, created_at FROM reservations WHERE result IS NULL ORDER BY id"):
            minutes_elapsed = elapsed(row[10])
            members = [{"id": item, "phase_round": round_no} for item, round_no in con.execute("SELECT outcome_id, round FROM reservation_outcomes WHERE reservation_id = ? ORDER BY outcome_id", (row[0],))]
            active.append({"reservation": row[0], "ticket": row[1], "kind": row[2], "criteria": row[3], "purpose": row[4], "expected": row[5], "minutes": row[6], "decision": row[7], "changed_approach": row[8], "exception": row[9], "created_at": row[10], "elapsed_minutes": round(minutes_elapsed, 6), "overdue": minutes_elapsed > row[6], "outcomes": members})
        decisions = [{"reservation": item[0], "ticket": item[1], "kind": item[2], "decision": item[3], "changed_approach": item[4], "exception": item[5]} for item in con.execute("SELECT id, ticket, kind, decision, changed_approach, exception FROM reservations WHERE decision IS NOT NULL ORDER BY id")]
    except (sqlite3.Error, GuardError) as error:
        if isinstance(error, GuardError): raise
        raise GuardError("status unavailable: %s" % error)
    finally:
        close(con)
    return {"ok": True, "outcomes": outcomes, "active_reservations": active, "decisions": decisions, "rounds_note": "rounds count reservations, not external calls or product acceptance"}


def v1_is_valid(con):
    tables = {row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    if tables != set(V1_TABLES): return False
    for table, required in V1_TABLES.items():
        if not required.issubset({row[1] for row in con.execute("PRAGMA table_info(%s)" % table)}): return False
    return not con.execute("PRAGMA foreign_key_check").fetchone()


def migrate(args):
    con = connect(args.database, required_version="1")
    try:
        con.execute("BEGIN IMMEDIATE")
        if not v1_is_valid(con): raise GuardError("database schema is unsupported or malformed")
        con.execute("ALTER TABLE reservations ADD COLUMN kind TEXT")
        con.execute("UPDATE reservations SET kind = 'product'")
        con.execute("CREATE TABLE outcome_phases (outcome_id TEXT NOT NULL REFERENCES outcomes(id), kind TEXT NOT NULL CHECK(kind IN ('plan', 'product')), rounds INTEGER NOT NULL DEFAULT 0 CHECK(rounds >= 0), PRIMARY KEY (outcome_id, kind))")
        con.execute("CREATE TABLE registrations (outcome_id TEXT PRIMARY KEY REFERENCES outcomes(id), reason TEXT NOT NULL, registered_at TEXT NOT NULL)")
        con.execute("INSERT INTO outcome_phases(outcome_id, kind, rounds) SELECT id, 'product', rounds FROM outcomes")
        con.execute("INSERT INTO outcome_phases(outcome_id, kind, rounds) SELECT id, 'plan', 0 FROM outcomes")
        con.execute("INSERT INTO registrations(outcome_id, reason, registered_at) SELECT id, 'migration from schema v1', ? FROM outcomes", (now(),))
        con.execute("UPDATE meta SET value = '2' WHERE key = 'schema_version'"); con.commit()
    except (GuardError, sqlite3.Error) as error:
        rollback(con)
        if isinstance(error, GuardError): raise
        raise GuardError("migration denied: %s" % error)
    finally:
        close(con)
    return {"ok": True, "migrated": True, "rounds_note": "v1 reservations were conservatively assigned kind product"}


def parser():
    root = JsonParser(description=__doc__); commands = root.add_subparsers(dest="command", required=True)
    init_parser = commands.add_parser("init"); init_parser.add_argument("database"); init_parser.add_argument("--outcomes", nargs="+", required=True)
    reserve_parser = commands.add_parser("reserve"); reserve_parser.add_argument("database"); reserve_parser.add_argument("--outcomes", nargs="+", required=True); reserve_parser.add_argument("--ticket", required=True); reserve_parser.add_argument("--kind", choices=("plan", "product"), default="product"); reserve_parser.add_argument("--criteria", required=True); reserve_parser.add_argument("--purpose", required=True); reserve_parser.add_argument("--expected", required=True); reserve_parser.add_argument("--minutes", required=True); reserve_parser.add_argument("--decision"); reserve_parser.add_argument("--changed-approach"); reserve_parser.add_argument("--exception")
    add_parser = commands.add_parser("add-outcomes"); add_parser.add_argument("database"); add_parser.add_argument("--outcomes", nargs="+", required=True); add_parser.add_argument("--reason", required=True)
    finish_parser = commands.add_parser("finish"); finish_parser.add_argument("database"); finish_parser.add_argument("--reservation", required=True); finish_parser.add_argument("--result", required=True); finish_parser.add_argument("--evidence", required=True)
    status_parser = commands.add_parser("status"); status_parser.add_argument("database")
    migrate_parser = commands.add_parser("migrate"); migrate_parser.add_argument("database")
    return root


def main(argv=None):
    try:
        args = parser().parse_args(argv)
        return emit({"init": init, "reserve": reserve, "add-outcomes": add_outcomes, "finish": finish, "status": status, "migrate": migrate}[args.command](args))
    except GuardError as error:
        return emit({"ok": False, "reason": str(error)}, 2)


if __name__ == "__main__":
    sys.exit(main())
