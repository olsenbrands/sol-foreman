import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = os.path.dirname(os.path.dirname(__file__))
SCRIPT = os.path.join(ROOT, "skills", "sol-foreman", "scripts", "review_guard.py")


class ReviewGuardTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.directory.name, "guard.sqlite")

    def tearDown(self):
        self.directory.cleanup()

    def cli(self, *args, expect=0):
        done = subprocess.run([sys.executable, SCRIPT, *args], text=True, capture_output=True)
        self.assertEqual(done.returncode, expect, done.stderr + done.stdout)
        return json.loads(done.stdout)

    def init(self, *outcomes):
        return self.cli("init", self.db, "--outcomes", *outcomes)

    def reserve(self, *outcomes, ticket="review", kind="product", extra=(), expect=0):
        return self.cli("reserve", self.db, "--outcomes", *outcomes, "--ticket", ticket, "--kind", kind, "--criteria", "objective evidence", "--purpose", "bounded review", "--expected", "report", "--minutes", "15", *extra, expect=expect)

    def finish(self, reservation, result="pass"):
        return self.cli("finish", self.db, "--reservation", str(reservation), "--result", result, "--evidence", "recorded evidence")

    def status(self):
        return self.cli("status", self.db)

    def test_plan_and_product_counters_are_separate(self):
        self.init("A")
        plan = self.reserve("A", ticket="plan", kind="plan"); self.finish(plan["reservation"])
        product_one = self.reserve("A", ticket="product-1"); self.finish(product_one["reservation"])
        product_two = self.reserve("A", ticket="product-2")
        self.assertEqual(product_two["outcomes"], [{"id": "A", "phase_round": 2, "total_round": 3}])
        self.assertEqual(self.status()["outcomes"], [{"id": "A", "rounds": 3, "phase_rounds": {"plan": 1, "product": 2}}])

    def test_product_round_three_and_four_are_gated(self):
        self.init("A")
        for number in range(2):
            item = self.reserve("A", ticket="r%d" % number); self.finish(item["reservation"], "fail")
        self.assertIn("decision", self.reserve("A", ticket="r3", expect=2)["reason"])
        third = self.reserve("A", ticket="r3", extra=("--decision", "change route", "--changed-approach", "new proof")); self.finish(third["reservation"], "incomplete")
        self.assertIn("exception", self.reserve("A", ticket="r4", extra=("--decision", "bounded exception", "--changed-approach", "separate verification"), expect=2)["reason"])
        fourth = self.reserve("A", ticket="r4", extra=("--decision", "bounded exception", "--changed-approach", "separate verification", "--exception", "one final isolated check"))
        self.assertEqual(fourth["outcomes"][0], {"id": "A", "phase_round": 4, "total_round": 4})

    def test_phase_batching_is_atomic(self):
        self.init("A", "B")
        denied = self.reserve("A", "missing", ticket="batch", kind="plan", expect=2)
        self.assertIn("unknown", denied["reason"])
        self.assertEqual(self.status()["outcomes"], [{"id": "A", "rounds": 0, "phase_rounds": {"plan": 0, "product": 0}}, {"id": "B", "rounds": 0, "phase_rounds": {"plan": 0, "product": 0}}])

    def test_ticket_alias_and_active_reservation_are_rejected(self):
        self.init("A", "B")
        active = self.reserve("A", ticket="same")
        self.assertIn("active", self.reserve("A", ticket="other", expect=2)["reason"])
        self.finish(active["reservation"])
        self.assertIn("different original", self.reserve("B", ticket="same", expect=2)["reason"])

    def test_add_outcomes_is_nonresetting_and_all_or_nothing(self):
        self.init("A")
        item = self.reserve("A"); self.finish(item["reservation"], "not-started")
        added = self.cli("add-outcomes", self.db, "--outcomes", "B", "C", "--reason", "new authorized scope")
        self.assertEqual(added["outcomes"], ["B", "C"])
        self.assertIn("already exist", self.cli("add-outcomes", self.db, "--outcomes", "A", "D", "--reason", "mixed", expect=2)["reason"])
        state = self.status()["outcomes"]
        self.assertEqual(state[0]["rounds"], 1)
        self.assertEqual([row["id"] for row in state], ["A", "B", "C"])
        self.assertEqual(state[2]["rounds"], 0)

    def test_duplicate_and_invalid_input_do_not_mutate(self):
        self.assertIn("unique", self.cli("init", self.db, "--outcomes", "A", "A", expect=2)["reason"])
        self.init("A")
        self.assertIn("unique", self.cli("add-outcomes", self.db, "--outcomes", "B", "B", "--reason", "new", expect=2)["reason"])
        for minutes in ("nan", "inf", "0", "-1"):
            self.assertIn("minutes", self.cli("reserve", self.db, "--outcomes", "A", "--ticket", "t" + minutes, "--criteria", "c", "--purpose", "p", "--expected", "e", "--minutes", minutes, expect=2)["reason"])
        self.assertEqual(self.status()["outcomes"][0]["rounds"], 0)

    def test_bad_finishes_and_missing_or_malformed_database_fail_closed(self):
        self.assertIn("missing", self.cli("status", self.db, expect=2)["reason"])
        with open(self.db, "w") as handle: handle.write("not sqlite")
        self.assertIn("database", self.cli("status", self.db, expect=2)["reason"])
        os.unlink(self.db); self.init("A")
        item = self.reserve("A")
        self.assertIn("unknown", self.cli("finish", self.db, "--reservation", "999", "--result", "pass", "--evidence", "x", expect=2)["reason"])
        self.finish(item["reservation"])
        self.assertIn("terminal", self.cli("finish", self.db, "--reservation", str(item["reservation"]), "--result", "pass", "--evidence", "x", expect=2)["reason"])

    def test_status_reports_timestamp_elapsed_and_overdue_without_enforcement(self):
        self.init("A")
        item = self.reserve("A", ticket="timed")
        con = sqlite3.connect(self.db)
        con.execute("UPDATE reservations SET created_at = '2000-01-01T00:00:00+00:00' WHERE id = ?", (item["reservation"],)); con.commit(); con.close()
        active = self.status()["active_reservations"][0]
        self.assertEqual(active["created_at"], "2000-01-01T00:00:00+00:00")
        self.assertGreater(active["elapsed_minutes"], active["minutes"])
        self.assertTrue(active["overdue"])

    def test_concurrent_reservations_only_one_wins(self):
        self.init("A")
        command = [sys.executable, SCRIPT, "reserve", self.db, "--outcomes", "A", "--ticket", "parallel", "--criteria", "c", "--purpose", "p", "--expected", "e", "--minutes", "1"]
        first = subprocess.Popen(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        second = subprocess.Popen(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        replies = [json.loads(process.communicate()[0]) for process in (first, second)]
        self.assertEqual(sum(reply["ok"] for reply in replies), 1)
        self.assertEqual(self.status()["outcomes"][0]["rounds"], 1)

    def test_init_publication_failure_leaves_no_target_or_temp(self):
        spec = importlib.util.spec_from_file_location("review_guard_test_module", SCRIPT)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        target = os.path.join(self.directory.name, "publication.sqlite")
        args = type("Args", (), {"database": target, "outcomes": ["A"]})()
        with mock.patch.object(module.os, "link", side_effect=OSError("injected publication failure")):
            with self.assertRaises(module.GuardError): module.init(args)
        self.assertFalse(os.path.exists(target))
        self.assertEqual(os.listdir(self.directory.name), [])

    def test_existing_file_init_is_preserved(self):
        with open(self.db, "w") as handle: handle.write("keep me")
        self.assertIn("overwrite", self.cli("init", self.db, "--outcomes", "A", expect=2)["reason"])
        with open(self.db) as handle: self.assertEqual(handle.read(), "keep me")

    def test_v1_migration_preserves_history_and_active_reservation(self):
        legacy = os.path.join(self.directory.name, "legacy.sqlite")
        con = sqlite3.connect(legacy)
        con.executescript("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL); CREATE TABLE outcomes (id TEXT PRIMARY KEY, rounds INTEGER NOT NULL DEFAULT 0); CREATE TABLE tickets (ticket TEXT PRIMARY KEY, outcome_key TEXT NOT NULL); CREATE TABLE reservations (id INTEGER PRIMARY KEY, ticket TEXT NOT NULL, criteria TEXT NOT NULL, purpose TEXT NOT NULL, expected TEXT NOT NULL, minutes REAL NOT NULL, decision TEXT, changed_approach TEXT, exception TEXT, result TEXT, evidence TEXT, created_at TEXT NOT NULL, finished_at TEXT); CREATE TABLE reservation_outcomes (reservation_id INTEGER NOT NULL REFERENCES reservations(id), outcome_id TEXT NOT NULL REFERENCES outcomes(id), round INTEGER NOT NULL, PRIMARY KEY (reservation_id, outcome_id));")
        con.execute("INSERT INTO meta VALUES ('schema_version', '1')"); con.execute("INSERT INTO outcomes VALUES ('A', 2)"); con.execute("INSERT INTO tickets VALUES ('legacy', '[\\\"A\\\"]')")
        con.execute("INSERT INTO reservations(id,ticket,criteria,purpose,expected,minutes,created_at) VALUES (1,'legacy','c','p','e',10,'2026-01-01T00:00:00+00:00')"); con.execute("INSERT INTO reservation_outcomes VALUES (1,'A',2)"); con.commit(); con.close()
        self.assertIn("run migrate", self.cli("status", legacy, expect=2)["reason"])
        self.assertTrue(self.cli("migrate", legacy)["migrated"])
        migrated = self.cli("status", legacy)
        self.assertEqual(migrated["outcomes"], [{"id": "A", "rounds": 2, "phase_rounds": {"plan": 0, "product": 2}}])
        self.assertEqual(migrated["active_reservations"][0]["kind"], "product")


if __name__ == "__main__":
    unittest.main()
