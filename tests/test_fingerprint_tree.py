import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "skills/sol-foreman/scripts/fingerprint_tree.py"
sys.path.insert(0, str(SCRIPT.parent))
import fingerprint_tree  # noqa: E402


class FingerprintTreeTests(unittest.TestCase):
    def test_manifest_is_stable_and_covers_hidden_untracked_content(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            for root in (Path(first), Path(second)):
                (root / ".hidden").write_text("secret-free\n", encoding="utf-8")
                (root / "nested").mkdir()
                (root / "nested/data.txt").write_text("value\n", encoding="utf-8")
                (root / ".git").mkdir()
                (root / ".git/volatile").write_text(str(root), encoding="utf-8")

            one = fingerprint_tree.fingerprint(Path(first), (".git",), True)
            two = fingerprint_tree.fingerprint(Path(second), (".git",), True)

        self.assertEqual(one, two)
        self.assertEqual([entry["path"] for entry in one["entries"]], [".hidden", "nested", "nested/data.txt"])

    def test_content_mode_symlink_and_custom_exclude_affect_expected_fields(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "target.txt"
            target.write_text("one\n", encoding="utf-8")
            ignored = root / "cache"
            ignored.mkdir()
            (ignored / "item").write_text("ignored\n", encoding="utf-8")
            if hasattr(os, "symlink"):
                os.symlink("target.txt", root / "link")

            before = fingerprint_tree.fingerprint(root, (".git", "cache"), True)
            target.write_text("two\n", encoding="utf-8")
            target.chmod(stat.S_IRUSR | stat.S_IWUSR)
            after = fingerprint_tree.fingerprint(root, (".git", "cache"), True)

        self.assertNotEqual(before["digest"], after["digest"])
        self.assertNotIn("cache", {entry["path"] for entry in after["entries"]})
        if hasattr(os, "symlink"):
            link = next(entry for entry in after["entries"] if entry["path"] == "link")
            self.assertEqual(link["path"], "link")
            self.assertEqual(link["type"], "symlink")
            self.assertEqual(link["target"], "target.txt")

    def test_cli_digest_matches_library_and_rejects_invalid_exclude(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "file.txt").write_text("value\n", encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "--manifest", str(root)],
                capture_output=True,
                text=True,
                check=False,
            )
            invalid = subprocess.run(
                [sys.executable, str(SCRIPT), "--exclude", "../outside", str(root)],
                capture_output=True,
                text=True,
                check=False,
            )
            expected = fingerprint_tree.fingerprint(root, (".git",), True)

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout), expected)
        self.assertNotEqual(invalid.returncode, 0)
        self.assertIn("invalid relative exclude", invalid.stderr)


if __name__ == "__main__":
    unittest.main()
