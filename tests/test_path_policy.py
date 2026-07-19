import os
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "skills/sol-foreman/scripts"
sys.path.insert(0, str(SCRIPT_DIR))
import path_policy  # noqa: E402


class PathPolicyTests(unittest.TestCase):
    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_resolved_scope_identity_collapses_internal_aliases(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "src").mkdir()
            try:
                os.symlink("src", root / "alias")
            except OSError as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            direct = path_policy.resolved_scope_identity(root, "src/file.py")
            alias = path_policy.resolved_scope_identity(root, "alias/file.py")
        self.assertEqual(direct, "src/file.py")
        self.assertEqual(alias, direct)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_resolved_scope_identity_rejects_metadata_and_external_aliases(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            outside = Path(temporary) / "outside"
            root.mkdir()
            outside.mkdir()
            (root / ".git").mkdir()
            try:
                os.symlink(".git", root / "metadata-alias")
                os.symlink(outside, root / "external-alias")
            except OSError as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            with self.assertRaisesRegex(ValueError, "excluded metadata"):
                path_policy.resolved_scope_identity(root, "metadata-alias/config")
            with self.assertRaisesRegex(ValueError, "outside the repository"):
                path_policy.resolved_scope_identity(root, "external-alias/file.py")


if __name__ == "__main__":
    unittest.main()
