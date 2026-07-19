#!/usr/bin/env python3
"""Maintain append-only Sol Foreman program state and enforce dispatch gates."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any, Optional

import path_policy
import preflight_ticket


SCHEMA_VERSION = 1
OUTCOMES = frozenset({"reported", "needs_fix", "rejected", "parked", "blocked"})
BREAKER_OUTCOMES = frozenset({"needs_fix", "rejected", "parked"})
TERMINAL_OUTCOMES = frozenset({"parked", "blocked"})
PARK_RECOVERY = frozenset({"escalated-and-failed", "lead-takeover-failed", "highest-suitable-seat-failed"})
RECOVERY_ACTIONS = frozenset({"correct-ticket", "add-evidence", "raise-effort", "escalate", "lead-takeover"})
PROVIDERS = frozenset({"native-codex", "codex-cli", "claude-cli", "lead"})
CAUSE_FAMILIES = frozenset(
    {
        "oversized-ticket", "bad-ticket", "capability-gap", "implementation-defect",
        "verification-harness", "shared-ownership", "external-dependency",
        "flaky-evidence", "unknown",
    }
)
REPORT_REASONS = frozenset(
    {
        "first_verified", "first_unsuccessful", "same_cause_breaker",
        "no_accepted_throughput", "pilot_result", "projection",
        "material_forecast_change", "verification_backlog", "attempt_exhausted",
        "all_items_verified",
    }
)


class EventError(ValueError):
    pass


def reject_constant(value: str) -> None:
    raise EventError(f"non-finite JSON value is forbidden: {value}")


def loads_json(value: str) -> Any:
    return json.loads(value, parse_constant=reject_constant)


def text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EventError(f"{field} must be a non-empty string")
    return value.strip()


def positive_int(value: Any, field: str, maximum: Optional[int] = None) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise EventError(f"{field} must be a positive integer")
    if maximum is not None and value > maximum:
        raise EventError(f"{field} must be no greater than {maximum}")
    return value


def number(value: Any, field: str) -> float:
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not math.isfinite(float(value))
        or value < 0
    ):
        raise EventError(f"{field} must be a finite non-negative number")
    return float(value)


def digest(value: Any, field: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise EventError(f"{field} must be a lowercase SHA-256 digest")
    return value


def telemetry(event: dict[str, Any], field: str) -> Optional[float]:
    if field in event:
        return number(event[field], field)
    if event.get(f"{field}_status") == "unavailable":
        text(event.get(f"{field}_reason"), f"{field}_reason")
        return None
    raise EventError(f"{field} must be a finite non-negative number or explicitly unavailable with a reason")


def string_values(value: Any, field: str, *, required: bool = False) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise EventError(f"{field} must be a list of non-empty strings")
    result = [item.strip() for item in value]
    if required and not result:
        raise EventError(f"{field} must contain at least one value")
    if len(result) != len(set(result)):
        raise EventError(f"{field} must not contain duplicates")
    return result


def route(event: dict[str, Any], field: str = "route") -> dict[str, str]:
    value = event.get(field)
    if not isinstance(value, dict):
        raise EventError(f"{field} must be an object")
    provider = value.get("provider")
    if provider not in PROVIDERS:
        raise EventError(f"{field}.provider must use the documented provider taxonomy")
    return {
        "provider": provider,
        "model": text(value.get("model"), f"{field}.model"),
        "effort": text(value.get("effort"), f"{field}.effort"),
        "evidence_sha256": digest(value.get("evidence_sha256"), f"{field}.evidence_sha256"),
    }


def projection_for(
    total_items: int,
    completed_items: set[str],
    costs: dict[str, float],
    telemetry_complete: dict[str, bool],
) -> dict[str, Any]:
    accepted = len(completed_items)
    remaining = max(total_items - accepted, 0)
    projection: dict[str, Any] = {"remaining_items": remaining}
    if accepted and telemetry_complete["worker_minutes"] and telemetry_complete["verification_minutes"]:
        observed_minutes = costs["worker_minutes"] + costs["verification_minutes"]
        per_item = round(observed_minutes / accepted, 2)
        projection["observed_work_minutes_per_completed_item"] = per_item
        projection["projected_additional_work_minutes"] = round(per_item * remaining, 2)
    else:
        projection["projected_additional_work_minutes"] = (
            "unavailable_until_first_completed_item" if not accepted else "unavailable_due_to_missing_telemetry"
        )
    if accepted and telemetry_complete["noncached_input_tokens"]:
        per_item_tokens = round(costs["noncached_input_tokens"] / accepted, 2)
        projection["observed_noncached_tokens_per_completed_item"] = per_item_tokens
        projection["projected_additional_noncached_input_tokens"] = round(per_item_tokens * remaining, 2)
    else:
        projection["projected_additional_noncached_input_tokens"] = (
            "unavailable_until_first_completed_item" if not accepted else "unavailable_due_to_missing_telemetry"
        )
    return projection


def load_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = loads_json(line)
        except (ValueError, RecursionError) as exc:
            raise EventError(f"invalid JSON on line {line_number}: {exc}") from exc
        if not isinstance(event, dict):
            raise EventError(f"line {line_number} must contain a JSON object")
        events.append(event)
    return events


def derive(events: list[dict[str, Any]]) -> dict[str, Any]:
    program_id: Optional[str] = None
    program_items: set[str] = set()
    total_items = 0
    current_plan: Optional[str] = None
    long_program = False
    pilot_limit = 0
    max_parallel = 1
    pilot_approved = True
    pilot_verified_index = -1
    pilot_halt: Optional[dict[str, Any]] = None
    attempt_exhausted: Optional[dict[str, Any]] = None
    completed = False

    dispatched_attempts: dict[tuple[str, int], str] = {}
    worker_by_attempt: dict[tuple[str, int], str] = {}
    route_by_attempt: dict[tuple[str, int], dict[str, str]] = {}
    write_identities_by_attempt: dict[tuple[str, int], list[str]] = {}
    workspace_by_attempt: dict[tuple[str, int], str] = {}
    items_by_attempt: dict[tuple[str, int], set[str]] = {}
    active_attempts: set[tuple[str, int]] = set()
    reported_attempts: set[tuple[str, int]] = set()
    outcome_by_attempt: dict[tuple[str, int], str] = {}
    plan_ticket_ids: set[str] = set()
    attempts_by_ticket: dict[str, set[int]] = defaultdict(set)
    recovery_by_ticket: dict[str, list[dict[str, Any]]] = defaultdict(list)
    terminal_tickets: dict[str, str] = {}
    verified_tickets: set[str] = set()
    completed_items: set[str] = set()
    unsuccessful: list[dict[str, Any]] = []
    costs = {"worker_minutes": 0.0, "verification_minutes": 0.0, "noncached_input_tokens": 0.0}
    telemetry_complete = {"worker_minutes": True, "verification_minutes": True, "noncached_input_tokens": True}
    breaker: Optional[dict[str, Any]] = None
    last_report_index = -1
    last_report_reasons: set[str] = set()
    last_elapsed_minutes = -1.0
    last_item_completion_index = -1
    last_process_transition_index = -1
    pending_report_reasons: list[str] = []
    failures_by_plan_cause: dict[tuple[str, str], set[str]] = defaultdict(set)
    failed_owner_by_plan_item: dict[tuple[str, str], str] = {}
    verifier_ids: set[str] = set()
    verifier_evidence_digests: set[str] = set()
    worker_receipt_digests: set[str] = set()

    def active_for_plan(plan_id: str) -> set[tuple[str, int]]:
        return {pair for pair in active_attempts if dispatched_attempts[pair] == plan_id}

    def mark_unsuccessful(event: dict[str, Any], pair: tuple[str, int], index: int, cause: str) -> None:
        nonlocal breaker, attempt_exhausted
        if not unsuccessful:
            pending_report_reasons.append("first_unsuccessful")
        unsuccessful.append(event)
        if event.get("outcome") in BREAKER_OUTCOMES:
            plan_id = dispatched_attempts[pair]
            failures_by_plan_cause[(plan_id, cause)].add(pair[0])
            for item_id in items_by_attempt[pair]:
                failed_owner_by_plan_item[(plan_id, item_id)] = pair[0]
            if len(failures_by_plan_cause[(plan_id, cause)]) >= 2 and breaker is None:
                breaker = {"plan_id": plan_id, "cause_family": cause, "event_index": index}
                pending_report_reasons.append("same_cause_breaker")
        if event.get("outcome") == "parked" or (
            pair[1] == 3 and event.get("outcome") in BREAKER_OUTCOMES
        ):
            attempt_exhausted = {"ticket_id": pair[0], "plan_id": dispatched_attempts[pair], "event_index": index}
            pending_report_reasons.append("attempt_exhausted")

    for index, event in enumerate(events):
        if event.get("schema_version") != SCHEMA_VERSION:
            raise EventError(f"event {index + 1}: schema_version must equal {SCHEMA_VERSION}")
        event_type = event.get("event")
        if completed:
            raise EventError(f"event {index + 1}: program_completed is terminal")

        if event_type == "program_started":
            if program_id is not None:
                raise EventError(f"event {index + 1}: program_started may occur only once")
            program_id = text(event.get("program_id"), "program_id")
            current_plan = text(event.get("plan_id"), "plan_id")
            total_items = positive_int(event.get("total_items"), "total_items")
            item_ids = string_values(event.get("program_item_ids"), "program_item_ids", required=True)
            if len(item_ids) != total_items:
                raise EventError(f"event {index + 1}: program_item_ids length must equal total_items")
            program_items = set(item_ids)
            if not isinstance(event.get("long_program"), bool):
                raise EventError(f"event {index + 1}: long_program must be true or false")
            long_program = event["long_program"]
            if total_items > 10 and not long_program:
                raise EventError(f"event {index + 1}: programs above 10 items must enable long_program controls")
            max_parallel = positive_int(event.get("max_parallel"), "max_parallel", 16)
            if long_program:
                pilot_limit = positive_int(event.get("pilot_limit"), "pilot_limit", 2)
                pilot_approved = False
            elif event.get("pilot_limit") not in (None, 0):
                raise EventError(f"event {index + 1}: pilot_limit must be 0 or omitted for a short program")
            continue

        if program_id is None or current_plan is None:
            raise EventError(f"event {index + 1}: program_started must be first")

        if event_type == "ticket_dispatched":
            if breaker is not None or attempt_exhausted is not None:
                raise EventError(f"event {index + 1}: dispatch is halted until report and replan")
            ticket_id = text(event.get("ticket_id"), "ticket_id")
            attempt = positive_int(event.get("attempt"), "attempt", 3)
            pair = (ticket_id, attempt)
            if ticket_id in terminal_tickets:
                raise EventError(f"event {index + 1}: {ticket_id} is terminal as {terminal_tickets[ticket_id]}")
            worker_id = text(event.get("worker_id"), "worker_id")
            dispatch_route = route(event)
            workspace_id = text(event.get("workspace_id"), "workspace_id")
            workspace_identity = digest(event.get("workspace_identity_sha256"), "workspace_identity_sha256")
            write_set = string_values(event.get("write_set"), "write_set", required=True)
            for scope in write_set:
                try:
                    path_policy.normalize_repo_path(scope, allow_globs=True)
                except ValueError as exc:
                    raise EventError(f"event {index + 1}: invalid write_set scope {scope!r}: {exc}") from exc
            write_identities = string_values(event.get("write_identities"), "write_identities", required=True)
            if len(write_identities) != len(write_set):
                raise EventError(f"event {index + 1}: write_identities must align with write_set")
            for identity in write_identities:
                try:
                    normalized_identity = path_policy.normalize_repo_path(identity, allow_globs=False).as_posix().casefold()
                except ValueError as exc:
                    raise EventError(f"event {index + 1}: invalid write identity {identity!r}: {exc}") from exc
                if identity != normalized_identity:
                    raise EventError(f"event {index + 1}: write identities must be canonical case-folded paths")
            dependencies = string_values(event.get("dependencies"), "dependencies")
            assigned_items = set(string_values(event.get("program_item_ids"), "program_item_ids", required=True))
            if not assigned_items.issubset(program_items):
                raise EventError(f"event {index + 1}: program_item_ids must come from program_started")
            if assigned_items & completed_items:
                raise EventError(f"event {index + 1}: completed program items cannot be redispatched")
            plan_id = text(event.get("plan_id"), "plan_id")
            if plan_id != current_plan:
                raise EventError(f"event {index + 1}: plan_id must match the active plan")
            if event.get("preflight_decision") != "READY":
                raise EventError(f"event {index + 1}: dispatch requires a READY preflight")
            digest(event.get("ticket_sha256"), "ticket_sha256")
            if pair in dispatched_attempts:
                raise EventError(f"event {index + 1}: ticket attempt was already dispatched")
            if any(active_ticket == ticket_id for active_ticket, _ in active_attempts):
                raise EventError(f"event {index + 1}: a ticket may have only one live attempt")
            expected_attempt = max(attempts_by_ticket[ticket_id], default=0) + 1
            if attempt != expected_attempt:
                raise EventError(f"event {index + 1}: next attempt for {ticket_id} must be {expected_attempt}")
            if any(dependency not in verified_tickets for dependency in dependencies):
                raise EventError(f"event {index + 1}: all dependencies must be verified before dispatch")
            for item_id in assigned_items:
                failed_owner = failed_owner_by_plan_item.get((current_plan, item_id))
                if failed_owner is not None and failed_owner != ticket_id:
                    raise EventError(
                        f"event {index + 1}: failed program item must retry its original ticket or wait for replan"
                    )
            for occupied_pair in active_attempts | reported_attempts:
                if assigned_items & items_by_attempt[occupied_pair]:
                    raise EventError(f"event {index + 1}: program item overlaps live or unverified ticket {occupied_pair[0]}")
            for occupied_pair in active_attempts | reported_attempts:
                if (
                    workspace_identity == workspace_by_attempt[occupied_pair]
                    and path_policy.scopes_overlap(write_identities, write_identities_by_attempt[occupied_pair])
                ):
                    raise EventError(
                        f"event {index + 1}: write set overlaps live or unverified ticket {occupied_pair[0]}"
                    )
            if len(active_attempts) + len(reported_attempts) >= max_parallel:
                raise EventError(f"event {index + 1}: max_parallel outstanding-work limit reached")
            if attempt > 1:
                actions = recovery_by_ticket[ticket_id]
                if not actions or actions[-1].get("after_attempt") != attempt - 1:
                    raise EventError(f"event {index + 1}: retry requires a recovery_action after the prior attempt")
                if attempt == 3:
                    action = actions[-1].get("action")
                    prior_route = route_by_attempt[(ticket_id, attempt - 1)]
                    if action == "lead-takeover":
                        if (
                            dispatch_route["provider"] != "lead"
                            or worker_id.casefold() == worker_by_attempt[(ticket_id, attempt - 1)].casefold()
                            or dispatch_route["evidence_sha256"] == prior_route["evidence_sha256"]
                        ):
                            raise EventError(f"event {index + 1}: lead takeover must bind a distinct lead route")
                    elif action == "escalate":
                        prior_signature = tuple(
                            value.casefold() for value in (prior_route["provider"], prior_route["model"], prior_route["effort"])
                        )
                        new_signature = tuple(
                            value.casefold() for value in (dispatch_route["provider"], dispatch_route["model"], dispatch_route["effort"])
                        )
                        if (
                            worker_id.casefold() == worker_by_attempt[(ticket_id, attempt - 1)].casefold()
                            or new_signature == prior_signature
                            or dispatch_route["evidence_sha256"] == prior_route["evidence_sha256"]
                        ):
                            raise EventError(f"event {index + 1}: escalation must change worker identity and capability route")
                    else:
                        raise EventError(f"event {index + 1}: third attempt requires capability escalation or lead takeover")

            is_new_ticket = ticket_id not in plan_ticket_ids
            if long_program and not pilot_approved:
                if pilot_verified_index >= 0:
                    raise EventError(f"event {index + 1}: review and approve the successful pilot before another dispatch")
                if is_new_ticket and len(plan_ticket_ids) >= pilot_limit:
                    raise EventError(f"event {index + 1}: pilot cap reached before accepted throughput")

            dispatched_attempts[pair] = current_plan
            worker_by_attempt[pair] = worker_id
            route_by_attempt[pair] = dispatch_route
            write_identities_by_attempt[pair] = write_identities
            workspace_by_attempt[pair] = workspace_identity
            items_by_attempt[pair] = assigned_items
            active_attempts.add(pair)
            attempts_by_ticket[ticket_id].add(attempt)
            plan_ticket_ids.add(ticket_id)
            pilot_halt = None
            continue

        if event_type == "ticket_outcome":
            ticket_id = text(event.get("ticket_id"), "ticket_id")
            attempt = positive_int(event.get("attempt"), "attempt", 3)
            pair = (ticket_id, attempt)
            if ticket_id in terminal_tickets:
                raise EventError(f"event {index + 1}: {ticket_id} is already terminal")
            if pair not in active_attempts:
                raise EventError(f"event {index + 1}: outcome requires the matching live attempt")
            outcome = event.get("outcome")
            if outcome not in OUTCOMES:
                raise EventError(f"event {index + 1}: invalid outcome")
            worker_receipt_digests.add(
                digest(event.get("worker_receipt_sha256"), "worker_receipt_sha256")
            )
            worker_minutes = telemetry(event, "worker_minutes")
            input_tokens = telemetry(event, "noncached_input_tokens")
            active_attempts.remove(pair)
            last_process_transition_index = index
            outcome_by_attempt[pair] = outcome
            if worker_minutes is None:
                telemetry_complete["worker_minutes"] = False
            else:
                costs["worker_minutes"] += worker_minutes
            if input_tokens is None:
                telemetry_complete["noncached_input_tokens"] = False
            else:
                costs["noncached_input_tokens"] += input_tokens
            if outcome == "reported":
                reported_attempts.add(pair)
                if len(reported_attempts) >= max_parallel:
                    pending_report_reasons.append("verification_backlog")
                continue

            cause = event.get("cause_family")
            if cause not in CAUSE_FAMILIES:
                raise EventError(f"event {index + 1}: cause_family must use the documented taxonomy")
            if outcome == "blocked" and (
                event.get("blocker_class") != "external" or cause not in {"external-dependency", "capability-gap"}
            ):
                raise EventError(
                    f"event {index + 1}: BLOCKED is reserved for an external dependency or capability; use rejected and replan for internal work"
                )
            if outcome == "parked":
                recovery = event.get("recovery")
                expected_actions = {
                    "escalated-and-failed": "escalate",
                    "lead-takeover-failed": "lead-takeover",
                    "highest-suitable-seat-failed": "escalate",
                }
                if recovery not in PARK_RECOVERY or not recovery_by_ticket[ticket_id]:
                    raise EventError(f"event {index + 1}: parked requires recorded escalation or lead takeover history")
                if recovery_by_ticket[ticket_id][-1].get("action") != expected_actions[recovery]:
                    raise EventError(f"event {index + 1}: parked recovery does not match recovery_action history")
            if outcome in TERMINAL_OUTCOMES:
                terminal_tickets[ticket_id] = outcome
            mark_unsuccessful(event, pair, index, cause)
            if (
                long_program and not pilot_approved and pilot_verified_index < 0
                and len(plan_ticket_ids) >= pilot_limit and not active_for_plan(current_plan)
                and not reported_attempts
            ):
                pilot_halt = {"plan_id": current_plan, "event_index": index}
                pending_report_reasons.extend(["pilot_result", "no_accepted_throughput"])
            continue

        if event_type == "recovery_action":
            ticket_id = text(event.get("ticket_id"), "ticket_id")
            after_attempt = positive_int(event.get("after_attempt"), "after_attempt", 3)
            pair = (ticket_id, after_attempt)
            if pair not in outcome_by_attempt or outcome_by_attempt[pair] not in {"needs_fix", "rejected"}:
                raise EventError(f"event {index + 1}: recovery_action requires a completed failed attempt")
            if any(active_ticket == ticket_id for active_ticket, _ in active_attempts):
                raise EventError(f"event {index + 1}: recovery_action cannot change a live ticket")
            action = event.get("action")
            if action not in RECOVERY_ACTIONS:
                raise EventError(f"event {index + 1}: action must use the documented recovery taxonomy")
            evidence = text(event.get("evidence"), "evidence")
            if len(evidence) < 20:
                raise EventError(f"event {index + 1}: recovery evidence must contain at least 20 characters")
            recovery_by_ticket[ticket_id].append({"after_attempt": after_attempt, "action": action, "evidence": evidence})
            continue

        if event_type in {"ticket_verified", "ticket_verification_failed"}:
            ticket_id = text(event.get("ticket_id"), "ticket_id")
            attempt = positive_int(event.get("attempt"), "attempt", 3)
            pair = (ticket_id, attempt)
            if ticket_id in terminal_tickets:
                raise EventError(f"event {index + 1}: {ticket_id} is already terminal")
            if pair not in reported_attempts:
                raise EventError(f"event {index + 1}: verification requires a reported worker attempt")
            verifier_id = text(event.get("verifier_id"), "verifier_id")
            if verifier_id.casefold() == worker_by_attempt[pair].casefold():
                raise EventError(f"event {index + 1}: builder and verifier identities must differ")
            verifier_evidence = digest(event.get("verifier_evidence_sha256"), "verifier_evidence_sha256")
            if verifier_evidence == route_by_attempt[pair]["evidence_sha256"]:
                raise EventError(f"event {index + 1}: verifier evidence must identify a distinct process or session")
            verifier_ids.add(verifier_id.casefold())
            verifier_evidence_digests.add(verifier_evidence)
            verification_minutes = telemetry(event, "verification_minutes")
            verification_tokens = telemetry(event, "verification_noncached_input_tokens")
            if verification_minutes is None:
                telemetry_complete["verification_minutes"] = False
            else:
                costs["verification_minutes"] += verification_minutes
            if verification_tokens is None:
                telemetry_complete["noncached_input_tokens"] = False
            else:
                costs["noncached_input_tokens"] += verification_tokens

            if event_type == "ticket_verified":
                if event.get("verdict") != "PASS":
                    raise EventError(f"event {index + 1}: only an independently reproduced PASS may be accepted")
                if event.get("lead_reviewed") is not True or event.get("processes_closed") is not True:
                    raise EventError(f"event {index + 1}: lead review and process closure are required")
                if event.get("verification_scope") not in {"slice", "integration"}:
                    raise EventError(f"event {index + 1}: verification_scope must be slice or integration")
                text(event.get("criteria_evidence_path"), "criteria_evidence_path")
                digest(event.get("criteria_evidence_sha256"), "criteria_evidence_sha256")
                digest(event.get("candidate_fingerprint"), "candidate_fingerprint")
                completed_now = set(string_values(event.get("completed_item_ids"), "completed_item_ids"))
                if not completed_now.issubset(items_by_attempt[pair]):
                    raise EventError(f"event {index + 1}: completed_item_ids must be assigned to this ticket")
                if completed_now & completed_items:
                    raise EventError(f"event {index + 1}: a program item may be completed only once")
                first_verified = not verified_tickets
                reported_attempts.remove(pair)
                last_process_transition_index = index
                if len(reported_attempts) < max_parallel:
                    pending_report_reasons = [
                        reason for reason in pending_report_reasons if reason != "verification_backlog"
                    ]
                terminal_tickets[ticket_id] = "verified"
                verified_tickets.add(ticket_id)
                completed_items.update(completed_now)
                if completed_now:
                    last_item_completion_index = index
                if first_verified:
                    pending_report_reasons.append("first_verified")
                if len(completed_items) == total_items:
                    pending_report_reasons.append("all_items_verified")
                if long_program and not pilot_approved and dispatched_attempts[pair] == current_plan:
                    if completed_now:
                        pilot_verified_index = index
                        pending_report_reasons.append("pilot_result")
                    elif len(plan_ticket_ids) >= pilot_limit and not active_for_plan(current_plan) and not reported_attempts:
                        pilot_halt = {"plan_id": current_plan, "event_index": index}
                        pending_report_reasons.extend(["pilot_result", "no_accepted_throughput"])
                continue

            if event.get("verdict") != "FAIL" or event.get("lead_reviewed") is not True:
                raise EventError(f"event {index + 1}: verification failure requires verifier FAIL and lead review")
            cause = event.get("cause_family")
            if cause not in CAUSE_FAMILIES:
                raise EventError(f"event {index + 1}: cause_family must use the documented taxonomy")
            text(event.get("finding_evidence_path"), "finding_evidence_path")
            digest(event.get("finding_evidence_sha256"), "finding_evidence_sha256")
            digest(event.get("candidate_fingerprint"), "candidate_fingerprint")
            reported_attempts.remove(pair)
            last_process_transition_index = index
            if len(reported_attempts) < max_parallel:
                pending_report_reasons = [
                    reason for reason in pending_report_reasons if reason != "verification_backlog"
                ]
            outcome_by_attempt[pair] = "rejected"
            failed_event = {**event, "outcome": "rejected"}
            mark_unsuccessful(failed_event, pair, index, cause)
            if (
                long_program and not pilot_approved and pilot_verified_index < 0
                and len(plan_ticket_ids) >= pilot_limit and not active_for_plan(current_plan)
                and not reported_attempts
            ):
                pilot_halt = {"plan_id": current_plan, "event_index": index}
                pending_report_reasons.extend(["pilot_result", "no_accepted_throughput"])
            continue

        if event_type == "progress_reported":
            reasons = event.get("reasons")
            if not isinstance(reasons, list) or not reasons or any(item not in REPORT_REASONS for item in reasons):
                raise EventError(f"event {index + 1}: reasons must use the documented report taxonomy")
            snapshot = event.get("snapshot")
            if not isinstance(snapshot, dict):
                raise EventError(f"event {index + 1}: progress report requires a metrics snapshot")
            expected_counts = {
                "accepted_items": len(completed_items),
                "verified_tickets": len(verified_tickets),
                "attempts": len(dispatched_attempts),
                "remaining_items": total_items - len(completed_items),
                "active_attempts": len(active_attempts),
                "reported_unverified": len(reported_attempts),
            }
            for field, expected in expected_counts.items():
                if snapshot.get(field) != expected:
                    raise EventError(f"event {index + 1}: snapshot {field} does not match state")
            elapsed = number(snapshot.get("elapsed_minutes"), "snapshot.elapsed_minutes")
            if elapsed < last_elapsed_minutes:
                raise EventError(f"event {index + 1}: elapsed_minutes must be monotonic")
            expected_projection = projection_for(total_items, completed_items, costs, telemetry_complete)
            if snapshot.get("projection") != expected_projection:
                raise EventError(f"event {index + 1}: snapshot projection does not match guarded state")
            projection_note = text(snapshot.get("projection_note"), "snapshot.projection_note")
            if len(projection_note) < 20:
                raise EventError(f"event {index + 1}: projection_note must contain at least 20 characters")
            last_elapsed_minutes = elapsed
            last_report_index = index
            last_report_reasons = set(reasons)
            pending_report_reasons = [reason for reason in pending_report_reasons if reason not in last_report_reasons]
            continue

        if event_type == "pilot_approved":
            if not long_program or pilot_approved:
                raise EventError(f"event {index + 1}: no pilot approval is pending")
            if breaker is not None or pilot_verified_index < 0 or not completed_items:
                raise EventError(f"event {index + 1}: pilot approval requires completed accepted throughput and no breaker")
            if last_report_index <= pilot_verified_index or not {"pilot_result", "projection"}.issubset(last_report_reasons):
                raise EventError(f"event {index + 1}: report pilot result and exact projection before approval")
            evidence = text(event.get("evidence"), "evidence")
            if len(evidence) < 20:
                raise EventError(f"event {index + 1}: pilot evidence must contain at least 20 characters")
            pilot_approved = True
            pilot_halt = None
            continue

        if event_type == "replanned":
            halts = [halt for halt in (breaker, pilot_halt, attempt_exhausted) if halt is not None]
            if not halts:
                raise EventError(f"event {index + 1}: replanned requires a breaker, exhausted pilot, or exhausted attempt budget")
            if active_attempts or reported_attempts:
                raise EventError(f"event {index + 1}: replan requires all writers and reported attempts to reach terminal review")
            required_reasons = {"projection"}
            if breaker:
                required_reasons.add("same_cause_breaker")
            if attempt_exhausted:
                required_reasons.add("attempt_exhausted")
            if pilot_halt:
                required_reasons.add("pilot_result")
            if (
                last_report_index <= max(
                    max(halt["event_index"] for halt in halts), last_process_transition_index
                )
                or not required_reasons.issubset(last_report_reasons)
            ):
                raise EventError(f"event {index + 1}: report the halt and exact projection before replanning")
            corrective_action = text(event.get("corrective_action"), "corrective_action")
            if len(corrective_action) < 20:
                raise EventError(f"event {index + 1}: corrective_action must contain at least 20 characters")
            new_plan = text(event.get("new_plan_id"), "new_plan_id")
            if new_plan == current_plan:
                raise EventError(f"event {index + 1}: new_plan_id must differ from the halted plan")
            if "max_parallel" in event:
                max_parallel = positive_int(event.get("max_parallel"), "max_parallel", 16)
            current_plan = new_plan
            plan_ticket_ids = set()
            breaker = None
            pilot_halt = None
            attempt_exhausted = None
            pilot_verified_index = -1
            pilot_approved = not long_program
            continue

        if event_type == "program_completed":
            if completed_items != program_items:
                raise EventError(f"event {index + 1}: every original program item must be completed")
            if active_attempts or reported_attempts:
                raise EventError(f"event {index + 1}: every worker and verifier process must be terminal")
            if last_report_index <= last_item_completion_index or "projection" not in last_report_reasons:
                raise EventError(f"event {index + 1}: report zero remaining work and exact projection before completion")
            if pending_report_reasons:
                raise EventError(f"event {index + 1}: all required progress reasons must be reported before completion")
            verifier_id = text(event.get("verifier_id"), "verifier_id")
            if verifier_id.casefold() in {worker.casefold() for worker in worker_by_attempt.values()}:
                raise EventError(f"event {index + 1}: final assembler/verifier must not be a builder")
            if verifier_id.casefold() in verifier_ids:
                raise EventError(f"event {index + 1}: final assembler/verifier must use a fresh verifier identity")
            final_verifier_evidence = digest(event.get("verifier_evidence_sha256"), "verifier_evidence_sha256")
            if final_verifier_evidence in {item["evidence_sha256"] for item in route_by_attempt.values()}:
                raise EventError(f"event {index + 1}: final verifier evidence must identify a non-builder process or session")
            if final_verifier_evidence in worker_receipt_digests:
                raise EventError(f"event {index + 1}: final verifier evidence must not reuse a builder receipt")
            if final_verifier_evidence in verifier_evidence_digests:
                raise EventError(f"event {index + 1}: final assembled verification must use fresh evidence")
            if event.get("verdict") != "PASS" or event.get("verification_scope") != "assembled":
                raise EventError(f"event {index + 1}: completion requires an assembled PASS")
            if (
                event.get("lead_reviewed") is not True
                or event.get("processes_closed") is not True
                or event.get("original_criteria_reconciled") is not True
            ):
                raise EventError(f"event {index + 1}: lead review, process closure, and original-criteria reconciliation are required")
            text(event.get("criteria_reconciliation_path"), "criteria_reconciliation_path")
            digest(event.get("criteria_reconciliation_sha256"), "criteria_reconciliation_sha256")
            digest(event.get("candidate_fingerprint"), "candidate_fingerprint")
            verification_minutes = telemetry(event, "verification_minutes")
            verification_tokens = telemetry(event, "verification_noncached_input_tokens")
            if verification_minutes is None:
                telemetry_complete["verification_minutes"] = False
            else:
                costs["verification_minutes"] += verification_minutes
            if verification_tokens is None:
                telemetry_complete["noncached_input_tokens"] = False
            else:
                costs["noncached_input_tokens"] += verification_tokens
            completed = True
            continue

        raise EventError(f"event {index + 1}: unknown event type {event_type!r}")

    projection = projection_for(total_items, completed_items, costs, telemetry_complete) if program_id else {}
    if not completed_items and len(unsuccessful) >= 2:
        pending_report_reasons.append("no_accepted_throughput")
    active_current = active_for_plan(current_plan) if current_plan else set()
    retryable = {
        ticket_id for ticket_id in plan_ticket_ids
        if ticket_id not in terminal_tickets
        and max(attempts_by_ticket[ticket_id], default=0) < 3
        and not any(pair[0] == ticket_id for pair in active_attempts | reported_attempts)
    }
    halted = breaker is not None or attempt_exhausted is not None
    capacity = len(active_attempts) + len(reported_attempts) < max_parallel
    remaining = max(total_items - len(completed_items), 0)
    if program_id is None or completed or halted or remaining == 0:
        allow_new_ticket = allow_retry = False
    elif long_program and not pilot_approved:
        allow_retry = bool(retryable) and pilot_verified_index < 0 and capacity
        allow_new_ticket = (
            pilot_verified_index < 0 and len(plan_ticket_ids) < pilot_limit and capacity and pilot_halt is None
        )
    else:
        allow_retry = bool(retryable) and capacity
        allow_new_ticket = capacity

    pilot_state = "not-required"
    if long_program:
        if pilot_approved:
            pilot_state = "approved"
        elif pilot_verified_index >= 0:
            pilot_state = "awaiting-review"
        elif reported_attempts:
            pilot_state = "awaiting-verification"
        elif pilot_halt:
            pilot_state = "exhausted"
        else:
            pilot_state = "running"

    completion_ready = (
        bool(program_id) and remaining == 0 and not active_attempts and not reported_attempts
        and last_report_index > last_item_completion_index and "projection" in last_report_reasons
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "program_id": program_id,
        "active_plan_id": current_plan,
        "total_items": total_items or None,
        "accepted_items": len(completed_items),
        "verified_tickets": len(verified_tickets),
        "completed_item_ids": sorted(completed_items),
        "remaining_items": remaining if program_id else None,
        "attempts": len(dispatched_attempts),
        "active_attempts": len(active_attempts),
        "active_current_plan_attempts": len(active_current),
        "reported_unverified": len(reported_attempts),
        "processes_closed": not active_attempts and not reported_attempts,
        "unsuccessful_outcomes": len(unsuccessful),
        "allow_dispatch": allow_new_ticket or allow_retry,
        "allow_new_ticket": allow_new_ticket,
        "allow_retry": allow_retry,
        "completion_ready": completion_ready,
        "completed": completed,
        "pilot_state": pilot_state,
        "breaker": breaker,
        "attempt_exhausted": attempt_exhausted,
        "reports_due": list(dict.fromkeys(pending_report_reasons)),
        "costs": {key: (round(value, 2) if telemetry_complete[key] else "unavailable") for key, value in costs.items()},
        "projection": projection,
    }


def read_event(path: Path) -> dict[str, Any]:
    payload = loads_json(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise EventError("event file must contain a JSON object")
    return payload


def atomic_append(path: Path, event: dict[str, Any]) -> None:
    existing = path.read_bytes() if path.exists() else b""
    if existing and not existing.endswith(b"\n"):
        raise EventError("event log has an incomplete final line")
    line = json.dumps(
        event, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8") + b"\n"
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(existing)
            handle.write(line)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def append_event(path: Path, event: dict[str, Any]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_name(f"{path.name}.lock")
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise EventError(f"event log is locked by another writer or a stale lock: {lock}") from exc
    try:
        os.close(descriptor)
        existing = load_events(path)
        result = derive([*existing, event])
        atomic_append(path, event)
        return result
    finally:
        try:
            lock.unlink()
        except OSError:
            pass


def dispatch_event(
    path: Path,
    ticket_path: Path,
    attempt: int,
    worker_id: str,
    provider: str,
    model: str,
    effort: str,
    route_evidence_sha256: str,
    repository_root: Path,
    workspace_id: str,
) -> dict[str, Any]:
    ticket = loads_json(ticket_path.read_text(encoding="utf-8"))
    result = preflight_ticket.evaluate(ticket)
    if result.get("decision") != "READY":
        raise EventError(f"ticket preflight returned {result.get('decision')}")
    if ticket.get("kind") not in preflight_ticket.EXECUTION_KINDS:
        raise EventError("program guard dispatch records execution tickets only")
    state = derive(load_events(path))
    plan_id = state.get("active_plan_id")
    if not plan_id:
        raise EventError("program_started must be recorded before dispatch")
    repository_root = repository_root.resolve(strict=True)
    workspace_identity = hashlib.sha256(
        os.path.normcase(str(repository_root)).casefold().encode("utf-8")
    ).hexdigest()
    write_identities = [
        path_policy.resolved_scope_identity(repository_root, scope)
        for scope in ticket["expected_paths"]
    ]
    event = {
        "schema_version": SCHEMA_VERSION,
        "event": "ticket_dispatched",
        "ticket_id": ticket["id"],
        "attempt": attempt,
        "worker_id": text(worker_id, "worker_id"),
        "workspace_id": text(workspace_id, "workspace_id"),
        "workspace_identity_sha256": workspace_identity,
        "route": {
            "provider": provider,
            "model": model,
            "effort": effort,
            "evidence_sha256": route_evidence_sha256,
        },
        "plan_id": plan_id,
        "preflight_decision": "READY",
        "ticket_sha256": result["ticket_sha256"],
        "write_set": ticket["expected_paths"],
        "write_identities": write_identities,
        "dependencies": ticket["dependencies"],
        "program_item_ids": ticket["program_item_ids"],
    }
    return append_event(path, event)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    status_parser = subparsers.add_parser("status", help="summarize an event log")
    status_parser.add_argument("state", type=Path)
    record_parser = subparsers.add_parser("record", help="validate and append one non-dispatch event")
    record_parser.add_argument("state", type=Path)
    record_parser.add_argument("event_file", type=Path)
    dispatch_parser = subparsers.add_parser("dispatch", help="preflight a ticket and record one attempt")
    dispatch_parser.add_argument("state", type=Path)
    dispatch_parser.add_argument("ticket", type=Path)
    dispatch_parser.add_argument("--attempt", required=True, type=int)
    dispatch_parser.add_argument("--worker-id", required=True)
    dispatch_parser.add_argument("--provider", required=True, choices=sorted(PROVIDERS))
    dispatch_parser.add_argument("--model", required=True)
    dispatch_parser.add_argument("--effort", required=True)
    dispatch_parser.add_argument("--route-evidence-sha256", required=True)
    dispatch_parser.add_argument("--repo-root", required=True, type=Path)
    dispatch_parser.add_argument("--workspace-id", required=True)
    args = parser.parse_args()

    try:
        if args.command == "status":
            result = derive(load_events(args.state))
        elif args.command == "dispatch":
            result = dispatch_event(
                args.state, args.ticket, args.attempt, args.worker_id,
                args.provider, args.model, args.effort, args.route_evidence_sha256,
                args.repo_root, args.workspace_id,
            )
        else:
            event = read_event(args.event_file)
            if event.get("event") == "ticket_dispatched":
                raise EventError("use the dispatch command so preflight cannot be skipped")
            result = append_event(args.state, event)
    except (OSError, ValueError, RecursionError) as exc:
        print(f"program guard failed: {exc}", file=sys.stderr)
        return 1
    json.dump(result, sys.stdout, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
