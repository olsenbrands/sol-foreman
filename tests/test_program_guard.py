import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "skills/sol-foreman/scripts/program_guard.py"
sys.path.insert(0, str(SCRIPT.parent))
import program_guard  # noqa: E402


def event(kind, **fields):
    return {"schema_version": 1, "event": kind, **fields}


def ready_ticket(ticket_id, item_id=None):
    item_id = item_id or ticket_id
    return {
        "schema_version": 1,
        "id": ticket_id,
        "kind": "implementation",
        "objective": "Implement one bounded behavior",
        "baseline": "abc123",
        "criteria": [{"id": "PC-1", "promise": "The named behavior is observable"}],
        "verification_gates": [{
            "criterion_id": "PC-1",
            "procedure": "python -m unittest tests.test_feature",
            "expected": "The command exits zero and the focused assertion passes",
        }],
        "subsystems": ["service"],
        "expected_paths": [f"src/{ticket_id}.py"],
        "risk_seams": [],
        "material_unknowns": [],
        "dependencies": [],
        "program_item_ids": [item_id],
        "estimated_minutes": 20,
        "recon_complete": True,
    }


class ProgramGuardTests(unittest.TestCase):
    def start(self, *, total=45, long=True, pilot_limit=2, max_parallel=4):
        fields = {
            "program_id": "P",
            "plan_id": "plan-1",
            "total_items": total,
            "program_item_ids": [f"ITEM-{index:02d}" for index in range(1, total + 1)],
            "long_program": long,
            "max_parallel": max_parallel,
        }
        if long:
            fields["pilot_limit"] = pilot_limit
        return [event("program_started", **fields)]

    def dispatch(self, ticket_id, *, item_ids=None, attempt=1, plan_id="plan-1", **extra):
        item_ids = item_ids or [ticket_id]
        write_set = extra.pop("write_set", [f"src/{ticket_id.casefold()}.py"])
        write_identities = extra.pop(
            "write_identities",
            [value.replace("\\", "/").casefold() for value in write_set],
        )
        payload = event(
            "ticket_dispatched",
            ticket_id=ticket_id,
            attempt=attempt,
            worker_id=f"worker-{ticket_id}-{attempt}",
            workspace_id="main-worktree",
            workspace_identity_sha256="1" * 64,
            route={
                "provider": "native-codex",
                "model": "sol",
                "effort": "high",
                "evidence_sha256": "a" * 64,
            },
            plan_id=plan_id,
            preflight_decision="READY",
            ticket_sha256="b" * 64,
            write_set=write_set,
            write_identities=write_identities,
            dependencies=[],
            program_item_ids=item_ids,
        )
        payload.update(extra)
        return payload

    def outcome(self, ticket_id, *, attempt=1, outcome="reported", cause=None, **extra):
        payload = event(
            "ticket_outcome",
            ticket_id=ticket_id,
            attempt=attempt,
            outcome=outcome,
            worker_receipt_sha256="c" * 64,
            worker_minutes=10,
            noncached_input_tokens=2000,
        )
        if cause is not None:
            payload["cause_family"] = cause
        payload.update(extra)
        return payload

    def reported(self, ticket_id, *, attempt=1, minutes=10, tokens=2000):
        return self.outcome(ticket_id, attempt=attempt, worker_minutes=minutes, noncached_input_tokens=tokens)

    def failure(self, ticket_id, *, attempt=1, cause="implementation-defect", outcome="needs_fix", **extra):
        return self.outcome(ticket_id, attempt=attempt, outcome=outcome, cause=cause, **extra)

    def verified(self, ticket_id, *, attempt=1, completed_item_ids=None, minutes=2, tokens=500):
        completed_item_ids = [ticket_id] if completed_item_ids is None else completed_item_ids
        return event(
            "ticket_verified",
            ticket_id=ticket_id,
            attempt=attempt,
            verifier_id=f"verifier-{ticket_id}",
            verifier_evidence_sha256="d" * 64,
            verdict="PASS",
            lead_reviewed=True,
            processes_closed=True,
            verification_scope="slice",
            completed_item_ids=completed_item_ids,
            criteria_evidence_path=f"evidence/{ticket_id}.json",
            criteria_evidence_sha256="e" * 64,
            candidate_fingerprint="f" * 64,
            verification_minutes=minutes,
            verification_noncached_input_tokens=tokens,
        )

    def verification_failed(self, ticket_id, *, attempt=1, cause="implementation-defect"):
        return event(
            "ticket_verification_failed",
            ticket_id=ticket_id,
            attempt=attempt,
            verifier_id=f"verifier-{ticket_id}",
            verifier_evidence_sha256="d" * 64,
            verdict="FAIL",
            lead_reviewed=True,
            cause_family=cause,
            finding_evidence_path=f"evidence/{ticket_id}-failure.json",
            finding_evidence_sha256="e" * 64,
            candidate_fingerprint="f" * 64,
            verification_minutes=2,
            verification_noncached_input_tokens=500,
        )

    def report(self, events, reasons, *, elapsed=60, mutate=None):
        state = program_guard.derive(events)
        snapshot = {
            "accepted_items": state["accepted_items"],
            "verified_tickets": state["verified_tickets"],
            "attempts": state["attempts"],
            "remaining_items": state["remaining_items"],
            "active_attempts": state["active_attempts"],
            "reported_unverified": state["reported_unverified"],
            "elapsed_minutes": elapsed,
            "projection": state["projection"],
            "projection_note": "Projection is copied from guarded accepted throughput and observed usage.",
        }
        if mutate:
            snapshot.update(mutate)
        return event("progress_reported", reasons=reasons, snapshot=snapshot)

    def complete_event(self):
        return event(
            "program_completed",
            verifier_id="final-independent-verifier",
            verifier_evidence_sha256="9" * 64,
            verdict="PASS",
            verification_scope="assembled",
            lead_reviewed=True,
            processes_closed=True,
            original_criteria_reconciled=True,
            criteria_reconciliation_path="evidence/final-criteria.json",
            criteria_reconciliation_sha256="8" * 64,
            candidate_fingerprint="7" * 64,
            verification_minutes=5,
            verification_noncached_input_tokens=800,
        )

    def accept(self, events, ticket_id, *, item_ids=None, attempt=1):
        events.extend([
            self.reported(ticket_id, attempt=attempt),
            self.verified(ticket_id, attempt=attempt, completed_item_ids=item_ids),
        ])

    def test_long_program_enforces_pilot_and_parallel_caps_independently(self):
        events = self.start(pilot_limit=2, max_parallel=1) + [self.dispatch("ITEM-01")]
        with self.assertRaisesRegex(program_guard.EventError, "max_parallel"):
            program_guard.derive([*events, self.dispatch("ITEM-02")])
        events = self.start(pilot_limit=2, max_parallel=3) + [self.dispatch("ITEM-01"), self.dispatch("ITEM-02")]
        with self.assertRaisesRegex(program_guard.EventError, "pilot cap"):
            program_guard.derive([*events, self.dispatch("ITEM-03")])

    def test_successful_pilot_requires_exact_report_and_approval(self):
        events = self.start(pilot_limit=1) + [self.dispatch("ITEM-01")]
        self.accept(events, "ITEM-01")
        with self.assertRaisesRegex(program_guard.EventError, "review and approve"):
            program_guard.derive([*events, self.dispatch("ITEM-02")])
        events.append(self.report(events, ["first_verified", "pilot_result", "projection"], elapsed=12))
        events.append(event("pilot_approved", evidence="Focused gate passed and forecast stayed within bounds."))
        self.assertEqual(program_guard.derive(events)["pilot_state"], "approved")

    def test_projection_report_rejects_fabrication_and_nonmonotonic_elapsed(self):
        events = self.start(pilot_limit=1) + [self.dispatch("ITEM-01")]
        self.accept(events, "ITEM-01")
        fabricated = self.report(
            events, ["first_verified", "pilot_result", "projection"], elapsed=12,
            mutate={"projection": {"remaining_items": 44, "projected_additional_work_minutes": 0}},
        )
        with self.assertRaisesRegex(program_guard.EventError, "projection does not match"):
            program_guard.derive([*events, fabricated])
        events.append(self.report(events, ["first_verified", "pilot_result", "projection"], elapsed=12))
        with self.assertRaisesRegex(program_guard.EventError, "monotonic"):
            program_guard.derive([*events, self.report(events, ["projection"], elapsed=11)])

    def test_verified_is_terminal_for_dispatch_and_late_verifier_fail(self):
        events = self.start(pilot_limit=1) + [self.dispatch("ITEM-01")]
        self.accept(events, "ITEM-01")
        with self.assertRaisesRegex(program_guard.EventError, "already terminal"):
            program_guard.derive([*events, self.verification_failed("ITEM-01")])
        with self.assertRaisesRegex(program_guard.EventError, "terminal as verified"):
            program_guard.derive([*events, self.dispatch("ITEM-01", attempt=2)])

    def test_replan_cannot_hide_old_live_or_reported_work(self):
        events = self.start(total=3, long=False, max_parallel=3) + [
            self.dispatch("ITEM-01"), self.dispatch("ITEM-02"), self.dispatch("ITEM-03")
        ]
        events.extend([
            self.failure("ITEM-02"), self.failure("ITEM-03"),
            self.report(events + [self.failure("ITEM-02"), self.failure("ITEM-03")],
                        ["first_unsuccessful", "same_cause_breaker", "projection"], elapsed=30),
        ])
        with self.assertRaisesRegex(program_guard.EventError, "all writers"):
            program_guard.derive([*events, event("replanned", new_plan_id="plan-2", corrective_action="Split the shared seam into isolated ownership units.")])
        self.accept(events, "ITEM-01")
        replan = event(
            "replanned", new_plan_id="plan-2",
            corrective_action="Split the shared seam into isolated ownership units.",
        )
        with self.assertRaisesRegex(program_guard.EventError, "exact projection"):
            program_guard.derive([*events, replan])
        events.append(self.report(events, ["same_cause_breaker", "projection"], elapsed=40))
        self.assertEqual(program_guard.derive([*events, replan])["active_plan_id"], "plan-2")

    def test_write_scopes_reject_root_globs_drive_paths_and_case_aliases(self):
        events = self.start(total=3, long=False, max_parallel=3) + [self.dispatch("ITEM-01")]
        for scope in ("./**", "C:outside.py", "**/*.py"):
            with self.subTest(scope=scope), self.assertRaisesRegex(program_guard.EventError, "invalid write_set"):
                program_guard.derive([*events, self.dispatch("ITEM-02", write_set=[scope])])
        events = self.start(total=2, long=False, max_parallel=2) + [
            self.dispatch("ITEM-01", write_set=["SRC/Orders.py"])
        ]
        with self.assertRaisesRegex(program_guard.EventError, "live or unverified"):
            program_guard.derive([*events, self.dispatch("ITEM-02", write_set=["src/orders.py"])])

    def test_reported_write_ownership_remains_reserved_until_verification(self):
        events = self.start(total=3, long=False, max_parallel=3) + [
            self.dispatch("ITEM-01", write_set=["src/shared.py"], write_identities=["src/shared.py"]),
            self.reported("ITEM-01"),
        ]
        with self.assertRaisesRegex(program_guard.EventError, "live or unverified"):
            program_guard.derive([
                *events,
                self.dispatch(
                    "ITEM-02", write_set=["SRC/shared.py"], write_identities=["src/shared.py"]
                ),
            ])

    def test_program_item_identity_prevents_slice_count_inflation(self):
        events = self.start(total=2, long=False, max_parallel=2) + [
            self.dispatch("slice-a", item_ids=["ITEM-01"])
        ]
        self.accept(events, "slice-a", item_ids=[])
        state = program_guard.derive(events)
        self.assertEqual(state["verified_tickets"], 1)
        self.assertEqual(state["accepted_items"], 0)
        events.append(self.dispatch("slice-b", item_ids=["ITEM-01"]))
        self.accept(events, "slice-b", item_ids=["ITEM-01"])
        self.assertEqual(program_guard.derive(events)["accepted_items"], 1)

    def test_verification_backlog_blocks_more_dispatch(self):
        events = self.start(total=4, long=False, max_parallel=2) + [
            self.dispatch("ITEM-01"), self.dispatch("ITEM-02"),
            self.reported("ITEM-01"), self.reported("ITEM-02"),
        ]
        state = program_guard.derive(events)
        self.assertFalse(state["allow_dispatch"])
        self.assertIn("verification_backlog", state["reports_due"])
        with self.assertRaisesRegex(program_guard.EventError, "outstanding-work"):
            program_guard.derive([*events, self.dispatch("ITEM-03")])

    def test_third_attempt_requires_real_route_change_and_exhaustion_can_replan(self):
        events = self.start(total=1, long=False, max_parallel=1) + [
            self.dispatch("ITEM-01"), self.failure("ITEM-01"),
            event("recovery_action", ticket_id="ITEM-01", after_attempt=1, action="add-evidence",
                  evidence="Attach the smallest deterministic failure reproduction."),
            self.dispatch("ITEM-01", attempt=2), self.failure("ITEM-01", attempt=2),
            event("recovery_action", ticket_id="ITEM-01", after_attempt=2, action="escalate",
                  evidence="Move the third attempt to a stronger independent route."),
        ]
        with self.assertRaisesRegex(program_guard.EventError, "change worker identity and capability route"):
            program_guard.derive([*events, self.dispatch("ITEM-01", attempt=3)])
        third = self.dispatch("ITEM-01", attempt=3)
        third["worker_id"] = "terra-worker"
        third["route"].update(model="terra", effort="max")
        with self.assertRaisesRegex(program_guard.EventError, "change worker identity and capability route"):
            program_guard.derive([*events, third])
        third["route"]["evidence_sha256"] = "6" * 64
        events.extend([third, self.failure("ITEM-01", attempt=3)])
        state = program_guard.derive(events)
        self.assertFalse(state["allow_retry"])
        self.assertEqual(state["attempt_exhausted"]["ticket_id"], "ITEM-01")
        events.append(self.report(events, ["first_unsuccessful", "attempt_exhausted", "projection"], elapsed=80))
        events.append(event("replanned", new_plan_id="plan-2", corrective_action="Replace the exhausted unit with a newly bounded implementation ticket."))
        self.assertEqual(program_guard.derive(events)["active_plan_id"], "plan-2")

    def test_parked_third_attempt_exhausts_and_halts_replacement_until_replan(self):
        events = self.start(total=1, long=False, max_parallel=1) + [
            self.dispatch("ITEM-01"), self.failure("ITEM-01"),
            event("recovery_action", ticket_id="ITEM-01", after_attempt=1, action="add-evidence",
                  evidence="Attach the exact first-attempt failure evidence."),
            self.dispatch("ITEM-01", attempt=2), self.failure("ITEM-01", attempt=2),
            event("recovery_action", ticket_id="ITEM-01", after_attempt=2, action="escalate",
                  evidence="Move the final attempt to a stronger independent route."),
        ]
        third = self.dispatch("ITEM-01", attempt=3)
        third["worker_id"] = "terra-worker"
        third["route"].update(model="terra", effort="max", evidence_sha256="6" * 64)
        events.extend([
            third,
            self.failure(
                "ITEM-01", attempt=3, outcome="parked", recovery="escalated-and-failed"
            ),
        ])
        state = program_guard.derive(events)
        self.assertEqual(state["attempt_exhausted"]["ticket_id"], "ITEM-01")
        with self.assertRaisesRegex(program_guard.EventError, "halted"):
            program_guard.derive([
                *events,
                self.dispatch("replacement", item_ids=["ITEM-01"]),
            ])

    def test_parked_second_attempt_requires_report_and_replan(self):
        events = self.start(total=1, long=False, max_parallel=1) + [
            self.dispatch("ITEM-01"),
            self.failure("ITEM-01"),
            event(
                "recovery_action",
                ticket_id="ITEM-01",
                after_attempt=1,
                action="escalate",
                evidence="Move the second attempt to the highest suitable independent route.",
            ),
            self.dispatch("ITEM-01", attempt=2),
            self.failure(
                "ITEM-01", attempt=2, outcome="parked", recovery="escalated-and-failed"
            ),
        ]
        state = program_guard.derive(events)
        self.assertEqual(state["attempt_exhausted"]["ticket_id"], "ITEM-01")
        with self.assertRaisesRegex(program_guard.EventError, "halted"):
            program_guard.derive([
                *events,
                self.dispatch("replacement", item_ids=["ITEM-01"]),
            ])
        events.append(
            self.report(events, ["first_unsuccessful", "attempt_exhausted", "projection"], elapsed=50)
        )
        events.append(event(
            "replanned",
            new_plan_id="plan-2",
            corrective_action="Replace the parked unit with a newly bounded implementation ticket.",
        ))
        self.assertEqual(program_guard.derive(events)["active_plan_id"], "plan-2")

    def test_replan_requires_every_simultaneous_halt_reason(self):
        events = self.start(total=3, long=True, pilot_limit=2, max_parallel=2) + [
            self.dispatch("ITEM-01"),
            self.dispatch("ITEM-02"),
            self.failure("ITEM-01", cause="implementation-defect"),
            self.failure("ITEM-02", cause="bad-ticket"),
            event(
                "recovery_action",
                ticket_id="ITEM-02",
                after_attempt=1,
                action="lead-takeover",
                evidence="The lead takes over after correcting the bounded ticket assumptions.",
            ),
            self.dispatch("ITEM-02", attempt=2),
            self.failure(
                "ITEM-02",
                attempt=2,
                cause="implementation-defect",
                outcome="parked",
                recovery="lead-takeover-failed",
            ),
        ]
        halted = program_guard.derive(events)
        self.assertIsNotNone(halted["breaker"])
        self.assertIsNotNone(halted["attempt_exhausted"])
        incomplete_report = self.report(
            events,
            ["first_unsuccessful", "same_cause_breaker", "pilot_result", "projection"],
            elapsed=70,
        )
        with self.assertRaisesRegex(program_guard.EventError, "report the halt"):
            program_guard.derive([
                *events,
                incomplete_report,
                event(
                    "replanned",
                    new_plan_id="plan-2",
                    corrective_action="Replace both failed slices with a corrected bounded pilot.",
                ),
            ])
        events.append(self.report(
            events,
            [
                "first_unsuccessful",
                "same_cause_breaker",
                "attempt_exhausted",
                "pilot_result",
                "no_accepted_throughput",
                "projection",
            ],
            elapsed=70,
        ))
        events.append(event(
            "replanned",
            new_plan_id="plan-2",
            corrective_action="Replace both failed slices with a corrected bounded pilot.",
        ))
        state = program_guard.derive(events)
        self.assertEqual(state["active_plan_id"], "plan-2")
        self.assertEqual(state["pilot_state"], "running")
        self.assertTrue(state["allow_dispatch"])

    def test_nonfinite_telemetry_is_rejected(self):
        events = self.start(pilot_limit=1) + [self.dispatch("ITEM-01")]
        malformed = self.reported("ITEM-01")
        malformed["worker_minutes"] = float("nan")
        with self.assertRaisesRegex(program_guard.EventError, "finite"):
            program_guard.derive([*events, malformed])
        with tempfile.TemporaryDirectory() as temporary:
            state = Path(temporary) / "events.jsonl"
            state.write_text(json.dumps(self.start(pilot_limit=1)[0]) + "\n" + '{"schema_version":1,"event":"x","value":NaN}\n', encoding="utf-8")
            with self.assertRaisesRegex(program_guard.EventError, "non-finite"):
                program_guard.load_events(state)

    def test_verifier_identity_is_casefolded_and_evidence_bound(self):
        events = self.start(pilot_limit=1) + [self.dispatch("ITEM-01"), self.reported("ITEM-01")]
        same = self.verified("ITEM-01")
        same["verifier_id"] = "WORKER-ITEM-01-1"
        with self.assertRaisesRegex(program_guard.EventError, "identities must differ"):
            program_guard.derive([*events, same])
        same_evidence = self.verified("ITEM-01")
        same_evidence["verifier_evidence_sha256"] = "a" * 64
        with self.assertRaisesRegex(program_guard.EventError, "distinct process"):
            program_guard.derive([*events, same_evidence])

    def test_program_completion_requires_zero_remaining_report_and_assembled_pass(self):
        events = self.start(total=1, long=False) + [self.dispatch("ITEM-01")]
        self.accept(events, "ITEM-01")
        with self.assertRaisesRegex(program_guard.EventError, "report zero remaining"):
            program_guard.derive([*events, self.complete_event()])
        events.append(self.report(events, ["first_verified", "all_items_verified", "projection"], elapsed=20))
        stale_final = self.complete_event()
        stale_final["verifier_id"] = "verifier-ITEM-01"
        stale_final["verifier_evidence_sha256"] = "d" * 64
        with self.assertRaisesRegex(program_guard.EventError, "fresh verifier identity"):
            program_guard.derive([*events, stale_final])
        reused_builder_receipt = self.complete_event()
        reused_builder_receipt["verifier_evidence_sha256"] = "c" * 64
        with self.assertRaisesRegex(program_guard.EventError, "builder receipt"):
            program_guard.derive([*events, reused_builder_receipt])
        state = program_guard.derive([*events, self.complete_event()])
        self.assertTrue(state["completed"])
        self.assertFalse(state["allow_dispatch"])
        with self.assertRaisesRegex(program_guard.EventError, "terminal"):
            program_guard.derive([*events, self.complete_event(), event("progress_reported")])

    def test_full_45_item_trace_completes_after_pilot_breaker_replan_and_assembled_gate(self):
        events = self.start(pilot_limit=1, max_parallel=3) + [self.dispatch("ITEM-01")]
        self.accept(events, "ITEM-01")
        events.append(self.report(events, ["first_verified", "pilot_result", "projection"], elapsed=12))
        events.append(event("pilot_approved", evidence="Pilot completed one original item with reproduced evidence."))
        events.extend([
            self.dispatch("ITEM-02"),
            self.dispatch("FAIL-03", item_ids=["ITEM-03"]),
            self.dispatch("FAIL-04", item_ids=["ITEM-04"]),
        ])
        self.accept(events, "ITEM-02")
        events.extend([self.failure("FAIL-03"), self.failure("FAIL-04")])
        self.assertIsNotNone(program_guard.derive(events)["breaker"])
        events.append(self.report(events, ["first_unsuccessful", "same_cause_breaker", "projection"], elapsed=50))
        events.append(event(
            "replanned", new_plan_id="plan-2", max_parallel=3,
            corrective_action="Replace failed shared slices with original-item-bounded ownership and a new pilot.",
        ))
        events.append(self.dispatch("ITEM-03", plan_id="plan-2"))
        self.accept(events, "ITEM-03")
        events.append(self.report(events, ["pilot_result", "projection"], elapsed=65))
        events.append(event("pilot_approved", evidence="Replanned pilot completed its original item without the repeated seam failure."))

        remaining_ids = ["ITEM-04", *[f"ITEM-{index:02d}" for index in range(5, 46)]]
        elapsed = 65
        for offset in range(0, len(remaining_ids), 3):
            wave = remaining_ids[offset:offset + 3]
            events.extend(self.dispatch(ticket_id, plan_id="plan-2") for ticket_id in wave)
            for ticket_id in wave:
                self.accept(events, ticket_id)
            elapsed += 15
        before_close = program_guard.derive(events)
        self.assertEqual(before_close["accepted_items"], 45)
        self.assertEqual(before_close["remaining_items"], 0)
        self.assertFalse(before_close["completed"])
        events.append(self.report(events, ["all_items_verified", "projection"], elapsed=elapsed))
        events.append(self.complete_event())
        final = program_guard.derive(events)
        self.assertTrue(final["completed"])
        self.assertEqual(final["accepted_items"], 45)
        self.assertEqual(final["attempts"], 47)
        self.assertTrue(final["processes_closed"])

    def test_dispatch_command_repreflights_and_binds_route(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = root / "events.jsonl"
            state.write_text(json.dumps(self.start(pilot_limit=1)[0]) + "\n", encoding="utf-8")
            ticket_path = root / "ticket.json"
            ticket_path.write_text(json.dumps(ready_ticket("ITEM-01")), encoding="utf-8")
            completed = subprocess.run([
                sys.executable, str(SCRIPT), "dispatch", str(state), str(ticket_path),
                "--attempt", "1", "--worker-id", "worker-1", "--provider", "native-codex",
                "--model", "sol", "--effort", "high", "--route-evidence-sha256", "a" * 64,
                "--repo-root", str(root), "--workspace-id", "main-worktree",
            ], capture_output=True, text=True)
            recorded = json.loads(state.read_text(encoding="utf-8").splitlines()[-1])
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(recorded["route"]["provider"], "native-codex")

    def test_event_lock_prevents_concurrent_or_stale_writer(self):
        with tempfile.TemporaryDirectory() as temporary:
            state = Path(temporary) / "events.jsonl"
            state.with_name("events.jsonl.lock").write_text("held\n", encoding="utf-8")
            with self.assertRaisesRegex(program_guard.EventError, "locked"):
                program_guard.append_event(state, self.start()[0])


if __name__ == "__main__":
    unittest.main()
