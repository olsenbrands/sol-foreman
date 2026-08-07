import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "skills/sol-foreman/scripts/run_cli_worker.py"
sys.path.insert(0, str(SCRIPT.parent))
import run_cli_worker  # noqa: E402


class RunCliWorkerTests(unittest.TestCase):
    def test_windows_suspended_creation_flag_matches_win32_contract(self):
        self.assertEqual(run_cli_worker.WINDOWS_CREATE_SUSPENDED, 0x00000004)

    def test_preserves_raw_stream_stderr_and_receipt_without_shell(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ticket = root / "ticket.txt"
            ticket.write_text("payload with $HOME and `uname`\n", encoding="utf-8")
            stdout = root / "run/stdout.bin"
            stderr = root / "run/stderr.bin"
            receipt = root / "run/receipt.json"
            child = (
                "import sys; data=sys.stdin.buffer.read(); "
                "sys.stdout.buffer.write(data); sys.stderr.write('diagnostic\\n')"
            )
            code = run_cli_worker.run(
                [sys.executable, "-c", child], root, ticket, stdout, stderr, receipt, []
            )
            payload = json.loads(receipt.read_text(encoding="utf-8"))
            captured = stdout.read_bytes()
            original = ticket.read_bytes()
        self.assertEqual(code, 0)
        self.assertEqual(captured, original)
        self.assertEqual(payload["exit_code"], 0)
        self.assertEqual(payload["status"], "terminal")
        self.assertIsInstance(payload["command"], list)

    def test_rejects_evidence_inside_protected_candidate(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = root / "candidate"
            candidate.mkdir()
            ticket = root / "ticket.txt"
            ticket.write_text("read only\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "outside protected root"):
                run_cli_worker.run(
                    [sys.executable, "-c", "pass"],
                    candidate,
                    ticket,
                    candidate / "stdout",
                    root / "stderr",
                    root / "receipt",
                    [candidate],
                )

    def test_protected_cwd_requires_explicit_read_only_allowance(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            candidate = root / "candidate"
            source.mkdir()
            candidate.mkdir()
            ticket = root / "ticket.txt"
            ticket.write_text("read only\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "read-only cwd allowance"):
                run_cli_worker.run(
                    [sys.executable, "-c", "pass"], source, ticket,
                    root / "stdout-1", root / "stderr-1", root / "receipt-1", [source, candidate],
                )
            code = run_cli_worker.run(
                [sys.executable, "-c", "pass"], candidate, ticket,
                root / "stdout-2", root / "stderr-2", root / "receipt-2", [source, candidate], [candidate],
            )
        self.assertEqual(code, 0)

    def test_cli_returns_child_exit_and_writes_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ticket = root / "ticket.txt"
            ticket.write_text("input\n", encoding="utf-8")
            receipt = root / "receipt.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--cwd",
                    str(root),
                    "--ticket",
                    str(ticket),
                    "--stdout",
                    str(root / "stdout"),
                    "--stderr",
                    str(root / "stderr"),
                    "--receipt",
                    str(receipt),
                    "--",
                    sys.executable,
                    "-c",
                    "raise SystemExit(7)",
                ],
                capture_output=True,
                text=True,
            )
            payload = json.loads(receipt.read_text(encoding="utf-8"))
        self.assertEqual(completed.returncode, 7)
        self.assertEqual(payload["exit_code"], 7)
        self.assertTrue(payload["process_tree_closed"])

    def test_refuses_to_overwrite_existing_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ticket = root / "ticket.txt"
            ticket.write_text("input\n", encoding="utf-8")
            stdout = root / "stdout"
            stdout.write_text("existing\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "already exists"):
                run_cli_worker.run(
                    [sys.executable, "-c", "pass"],
                    root,
                    ticket,
                    stdout,
                    root / "stderr",
                    root / "receipt",
                    [],
                )

    @unittest.skipIf(os.name == "nt", "symlink creation may require elevated Windows privileges")
    def test_rejects_symlink_artifact_and_ticket_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ticket = root / "ticket.txt"
            ticket.write_text("input\n", encoding="utf-8")
            dangling = root / "dangling-output"
            dangling.symlink_to(root / "outside-output")
            with self.assertRaisesRegex(ValueError, "is a symlink"):
                run_cli_worker.run(
                    [sys.executable, "-c", "pass"], root, ticket,
                    dangling, root / "stderr", root / "receipt", [],
                )
            ticket_link = root / "ticket-link.txt"
            ticket_link.symlink_to(ticket)
            with self.assertRaisesRegex(ValueError, "is a symlink"):
                run_cli_worker.run(
                    [sys.executable, "-c", "pass"], root, ticket_link,
                    root / "stdout", root / "stderr", root / "receipt", [],
                )

    def test_rejects_nonregular_artifact_and_keeps_existing_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ticket = root / "ticket.txt"
            ticket.write_text("input\n", encoding="utf-8")
            occupied = root / "occupied"
            occupied.mkdir()
            with self.assertRaisesRegex(ValueError, "not a regular file"):
                run_cli_worker.run(
                    [sys.executable, "-c", "pass"], root, ticket,
                    occupied, root / "stderr", root / "receipt", [],
                )
            existing = root / "existing"
            existing.write_text("preserve me\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "already exists"):
                run_cli_worker.run(
                    [sys.executable, "-c", "pass"], root, ticket,
                    existing, root / "stderr", root / "receipt", [],
                )
            self.assertEqual(existing.read_text(encoding="utf-8"), "preserve me\n")

    def test_receipt_redacts_gateway_url_in_command(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ticket = root / "ticket.txt"
            ticket.write_text("input\n", encoding="utf-8")
            receipt = root / "receipt.json"
            gateway = "https://token@gateway.example.invalid/v1"
            code = run_cli_worker.run(
                [sys.executable, "-c", "pass", gateway], root, ticket,
                root / "stdout", root / "stderr", receipt, [],
            )
            serialized = receipt.read_text(encoding="utf-8")
        self.assertEqual(code, 0)
        self.assertNotIn(gateway, serialized)
        self.assertIn("<redacted-gateway-url>", serialized)

    def test_raw_artifacts_redact_gateway_urls_without_changing_other_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ticket = root / "ticket.txt"
            ticket.write_text("input\n", encoding="utf-8")
            stdout = root / "stdout"
            stderr = root / "stderr"
            gateway = "https://token@gateway.example.invalid/v1"
            child = (
                "import sys; "
                f"sys.stdout.write('before {gateway} after\\n'); "
                f"sys.stderr.write('diagnostic {gateway}\\n')"
            )
            code = run_cli_worker.run(
                [sys.executable, "-c", child], root, ticket,
                stdout, stderr, root / "receipt", [],
            )
            stdout_text = stdout.read_text(encoding="utf-8")
            stderr_text = stderr.read_text(encoding="utf-8")
        self.assertEqual(code, 0)
        self.assertEqual(stdout_text, "before <redacted-gateway-url> after\n")
        self.assertEqual(stderr_text, "diagnostic <redacted-gateway-url>\n")

    def test_receipt_create_failure_kills_child_and_returns_nonzero(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ticket = root / "ticket.txt"
            ticket.write_text("input\n", encoding="utf-8")
            receipt = root / "receipt.json"
            original_atomic_json = run_cli_worker.atomic_json

            def fail_initial_receipt(path, payload, *, create=False):
                if create:
                    raise OSError("simulated receipt write failure")
                return original_atomic_json(path, payload, create=create)

            with mock.patch.object(run_cli_worker, "atomic_json", side_effect=fail_initial_receipt):
                code = run_cli_worker.run(
                    [sys.executable, "-c", "import time; time.sleep(60)"], root, ticket,
                    root / "stdout", root / "stderr", receipt, [],
                )
            payload = json.loads(receipt.read_text(encoding="utf-8"))
        self.assertNotEqual(code, 0)
        self.assertTrue(payload["process_tree_closed"])
        self.assertIn("simulated receipt write failure", payload["error"])

    @unittest.skipIf(os.name == "nt", "POSIX process-group assertion")
    def test_closes_descendant_process_group_after_direct_child_exits(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ticket = root / "ticket.txt"
            ticket.write_text("input\n", encoding="utf-8")
            pid_file = root / "descendant.pid"
            ready_file = root / "descendant.ready"
            descendant = (
                "import pathlib,signal,time; "
                "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
                f"pathlib.Path({str(ready_file)!r}).write_text('ready'); "
                "time.sleep(60)"
            )
            child = (
                "import pathlib,subprocess,sys,time; "
                f"p=subprocess.Popen([sys.executable,'-c',{descendant!r}]); "
                f"ready=pathlib.Path({str(ready_file)!r}); "
                "\nwhile not ready.exists(): time.sleep(0.01)\n"
                f"pathlib.Path({str(pid_file)!r}).write_text(str(p.pid))"
            )
            code = run_cli_worker.run(
                [sys.executable, "-c", child], root, ticket,
                root / "stdout", root / "stderr", root / "receipt", [],
            )
            descendant_pid = int(pid_file.read_text(encoding="utf-8"))
            payload = json.loads((root / "receipt").read_text(encoding="utf-8"))
            alive = True
            for _ in range(30):
                try:
                    os.kill(descendant_pid, 0)
                except ProcessLookupError:
                    alive = False
                    break
                time.sleep(0.05)
        self.assertEqual(code, 0)
        self.assertTrue(payload["process_tree_closed"])
        self.assertFalse(alive, "descendant survived wrapper process-tree closure")

    @unittest.skipIf(os.name == "nt", "POSIX detached-descendant assertion")
    def test_closes_detached_descendant_that_escapes_process_group(self):
        descendant_pid = None
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ticket = root / "ticket.txt"
            ticket.write_text("input\n", encoding="utf-8")
            pid_file = root / "detached.pid"
            ready_file = root / "detached.ready"
            descendant = (
                "import pathlib,signal,time; "
                "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
                f"pathlib.Path({str(ready_file)!r}).write_text('ready'); "
                "time.sleep(60)"
            )
            child = (
                "import pathlib,subprocess,sys,time; "
                f"p=subprocess.Popen([sys.executable,'-c',{descendant!r}], start_new_session=True); "
                f"ready=pathlib.Path({str(ready_file)!r}); "
                "\nwhile not ready.exists(): time.sleep(0.01)\n"
                f"pathlib.Path({str(pid_file)!r}).write_text(str(p.pid))"
            )
            try:
                code = run_cli_worker.run(
                    [sys.executable, "-c", child], root, ticket,
                    root / "stdout", root / "stderr", root / "receipt", [],
                )
                descendant_pid = int(pid_file.read_text(encoding="utf-8"))
                payload = json.loads((root / "receipt").read_text(encoding="utf-8"))
                alive = True
                for _ in range(30):
                    try:
                        os.kill(descendant_pid, 0)
                    except ProcessLookupError:
                        alive = False
                        break
                    time.sleep(0.05)
                self.assertEqual(code, 0)
                self.assertTrue(payload["process_tree_closed"])
                self.assertFalse(alive, "detached descendant survived token-tracked closure")
            finally:
                if descendant_pid is not None:
                    try:
                        os.kill(descendant_pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass


if __name__ == "__main__":
    unittest.main()
