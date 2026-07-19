import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "skills/sol-foreman/scripts/preflight_ticket.py"
sys.path.insert(0, str(SCRIPT.parent))
import preflight_ticket  # noqa: E402


def ticket(**overrides):
    payload = {
        "schema_version": 1,
        "id": "T-1",
        "kind": "implementation",
        "objective": "Implement one bounded behavior",
        "baseline": "abc123",
        "criteria": [{"id": "PC-1", "promise": "A focused behavior is observable"}],
        "verification_gates": [
            {
                "criterion_id": "PC-1",
                "procedure": "python -m unittest tests.test_feature",
                "expected": "The command exits zero and the focused assertion passes",
            }
        ],
        "subsystems": ["service"],
        "expected_paths": ["src/service.py", "tests/test_service.py"],
        "risk_seams": [],
        "material_unknowns": [],
        "dependencies": [],
        "program_item_ids": ["ITEM-01"],
        "estimated_minutes": 30,
        "recon_complete": True,
    }
    payload.update(overrides)
    return payload


class PreflightTicketTests(unittest.TestCase):
    def test_ready_bounded_ticket(self):
        result = preflight_ticket.evaluate(ticket())
        self.assertEqual(result["decision"], "READY")
        self.assertFalse(result["override_used"])

    def test_execution_unknowns_require_recon_not_user_blocker(self):
        result = preflight_ticket.evaluate(
            ticket(recon_complete=False, material_unknowns=["authoritative persistence contract"])
        )
        self.assertEqual(result["decision"], "RECON_REQUIRED")
        self.assertNotIn("BLOCKED", json.dumps(result))

    def test_compound_oversize_requires_decomposition(self):
        result = preflight_ticket.evaluate(
            ticket(
                criteria=[
                    {"id": f"PC-{index}", "promise": f"Observable criterion number {index}"}
                    for index in range(1, 7)
                ],
                verification_gates=[
                    {
                        "criterion_id": f"PC-{index}",
                        "procedure": f"run focused check number {index}",
                        "expected": f"observable result number {index} passes",
                    }
                    for index in range(1, 7)
                ],
                subsystems=["api", "ui", "migration"],
                expected_paths=[f"src/file_{index}.py" for index in range(12)],
                risk_seams=["schema", "auth", "provider"],
                estimated_minutes=90,
                first_checkpoint={"minutes": 15, "evidence": "first coherent diff and focused test"},
            )
        )
        self.assertEqual(result["decision"], "DECOMPOSE_REQUIRED")
        self.assertGreaterEqual(len(result["reasons"]), 2)

    def test_single_tripwire_requires_valid_checkpointed_override(self):
        paths = [f"src/file_{index}.py" for index in range(11)]
        review = preflight_ticket.evaluate(ticket(expected_paths=paths))
        ready = preflight_ticket.evaluate(
            ticket(
                expected_paths=paths,
                review_override={
                    "approved_by_lead": True,
                    "reason": "The files form one generated adapter family.",
                    "quality_case": "One owner avoids inconsistent mechanical edits.",
                },
                first_checkpoint={"minutes": 15, "evidence": "first completed adapter and focused gate"},
            )
        )
        self.assertEqual(review["decision"], "REVIEW_REQUIRED")
        self.assertEqual(ready["decision"], "READY")
        self.assertTrue(ready["override_used"])

    def test_override_rejects_missing_or_late_checkpoint(self):
        paths = [f"src/file_{index}.py" for index in range(11)]
        override = {
            "approved_by_lead": True,
            "reason": "The files form one generated adapter family.",
            "quality_case": "One owner avoids inconsistent mechanical edits.",
        }
        missing = preflight_ticket.evaluate(ticket(expected_paths=paths, review_override=override))
        late = preflight_ticket.evaluate(
            ticket(
                expected_paths=paths,
                review_override=override,
                first_checkpoint={"minutes": 999, "evidence": "an artifact far too late to control cost"},
            )
        )
        self.assertEqual(missing["decision"], "REVIEW_REQUIRED")
        self.assertIn("first_checkpoint must be an object", missing["reasons"])
        self.assertEqual(late["decision"], "INVALID")
        self.assertTrue(any("no later than" in reason for reason in late["reasons"]))

    def test_risky_ticket_requires_early_checkpoint(self):
        result = preflight_ticket.evaluate(ticket(risk_seams=["concurrency"]))
        self.assertEqual(result["decision"], "INVALID")
        self.assertIn("first_checkpoint must be an object", result["reasons"])

    def test_checkpoint_must_be_early_relative_to_estimate(self):
        result = preflight_ticket.evaluate(
            ticket(
                risk_seams=["concurrency"],
                estimated_minutes=40,
                first_checkpoint={"minutes": 21, "evidence": "first coherent concurrency reproduction"},
            )
        )
        self.assertEqual(result["decision"], "INVALID")
        self.assertIn("first_checkpoint.minutes must be no later than 20", result["reasons"])

    def test_structured_gates_must_cover_every_criterion(self):
        result = preflight_ticket.evaluate(
            ticket(
                criteria=[
                    {"id": "PC-1", "promise": "The first behavior is observable"},
                    {"id": "PC-2", "promise": "The second behavior is observable"},
                ]
            )
        )
        self.assertEqual(result["decision"], "INVALID")
        self.assertIn("criteria missing verification gates: PC-2", result["reasons"])

    def test_rejects_repository_wildcard_drive_relative_and_compound_labels(self):
        result = preflight_ticket.evaluate(
            ticket(expected_paths=["src/**", "C:outside.py"], subsystems=["ui + api"], risk_seams=["migration and provider"])
        )
        self.assertEqual(result["decision"], "INVALID")
        rendered = " ".join(result["reasons"])
        self.assertIn("recursive wildcards", rendered)
        self.assertIn("repository-relative", rendered)
        self.assertIn("split compound", rendered)

    def test_execution_ticket_requires_original_program_item_binding(self):
        result = preflight_ticket.evaluate(ticket(program_item_ids=[]))
        self.assertEqual(result["decision"], "INVALID")
        self.assertIn("program_item_ids must bind execution work to original program items", result["reasons"])

    def test_aggregate_boundary_dimensions_require_decomposition(self):
        criteria = [
            {"id": f"PC-{index}", "promise": f"Observable criterion number {index}"}
            for index in range(1, 6)
        ]
        gates = [
            {
                "criterion_id": f"PC-{index}",
                "procedure": f"run focused check number {index}",
                "expected": f"observable result number {index} passes",
            }
            for index in range(1, 6)
        ]
        result = preflight_ticket.evaluate(
            ticket(
                criteria=criteria,
                verification_gates=gates,
                subsystems=["api", "ui"],
                expected_paths=[f"src/file_{index}.py" for index in range(10)],
            )
        )
        self.assertEqual(result["decision"], "DECOMPOSE_REQUIRED")

    def test_cli_uses_machine_readable_exit_codes(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "ticket.json"
            path.write_text(json.dumps(ticket()), encoding="utf-8")
            ready = subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True)
            path.write_text(json.dumps(ticket(recon_complete=False)), encoding="utf-8")
            revise = subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True)
        self.assertEqual(ready.returncode, 0, ready.stderr)
        self.assertEqual(json.loads(ready.stdout)["decision"], "READY")
        self.assertEqual(revise.returncode, 2, revise.stderr)


if __name__ == "__main__":
    unittest.main()
