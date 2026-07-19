import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "skills/sol-foreman/scripts/materialize_candidate.py"
sys.path.insert(0, str(SCRIPT.parent))
import materialize_candidate  # noqa: E402


class MaterializeCandidateTests(unittest.TestCase):
    def test_copies_only_allowlisted_product_paths_and_excludes_metadata(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            (source / "src").mkdir()
            (source / "src/app.py").write_text("value = 1\n", encoding="utf-8")
            (source / "src/.foreman").mkdir()
            (source / "src/.foreman/private").write_text("ignore\n", encoding="utf-8")
            (source / "src/__pycache__").mkdir()
            (source / "src/__pycache__/app.pyc").write_bytes(b"cache")
            (source / "notes.txt").write_text("not selected\n", encoding="utf-8")
            destination = root / "candidate"
            result = materialize_candidate.materialize(
                source, destination, [materialize_candidate.normalize_relative("src")]
            )
            self.assertEqual(result["copied"], ["src"])
            self.assertTrue((destination / "src/app.py").is_file())
            self.assertFalse((destination / "src/.foreman").exists())
            self.assertFalse((destination / "src/__pycache__").exists())
            self.assertFalse((destination / "notes.txt").exists())

    def test_rejects_traversal_overlap_and_destination_inside_source(self):
        with self.assertRaises(ValueError):
            materialize_candidate.normalize_relative("../secret")
        for value in ("/etc/passwd", "C:\\Windows\\system.ini", "C:outside.txt", "\\\\server\\share\\file"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                materialize_candidate.normalize_relative(value)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            allowlist = root / "allowlist.json"
            allowlist.write_text(json.dumps(["src", "src/app.py"]), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "overlapping"):
                materialize_candidate.load_allowlist(allowlist)
            allowlist.write_text(json.dumps(["Src/App.py", "src/app.py"]), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "case-alias"):
                materialize_candidate.load_allowlist(allowlist)
            source = root / "source"
            source.mkdir()
            with self.assertRaisesRegex(ValueError, "inside source"):
                materialize_candidate.materialize(
                    source, source / "candidate", [materialize_candidate.normalize_relative("missing")]
                )

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_rejects_symlink_that_escapes_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            outside = root / "outside.txt"
            outside.write_text("outside\n", encoding="utf-8")
            try:
                os.symlink("../outside.txt", source / "escape")
            except OSError as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            with self.assertRaisesRegex(ValueError, "escaping symlink"):
                materialize_candidate.materialize(
                    source, root / "candidate", [materialize_candidate.normalize_relative("escape")]
                )

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_dereferences_safe_internal_symlink_consistently(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            (source / "target.txt").write_text("inside\n", encoding="utf-8")
            try:
                os.symlink("target.txt", source / "link.txt")
            except OSError as exc:
                self.skipTest(f"fixture symlink creation unavailable: {exc}")
            destination = root / "candidate"
            result = materialize_candidate.materialize(
                source,
                destination,
                [materialize_candidate.normalize_relative("link.txt")],
            )
            self.assertEqual((destination / "link.txt").read_text(encoding="utf-8"), "inside\n")
            self.assertEqual(result["transformations"][0]["action"], "dereferenced-internal-symlink")

    def test_rejects_case_variant_metadata_and_cache_paths(self):
        for value in (".GIT/config", "src/.Foreman/events.jsonl", "SRC/__PYCACHE__/x.pyc", "src/cache.PYC"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                materialize_candidate.normalize_relative(value)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_rejects_internal_symlinks_into_excluded_content(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            for directory, filename in ((".git", "config"), (".foreman", "events"), ("__pycache__", "x.pyc"), (".pytest_cache", "state")):
                (source / directory).mkdir()
                (source / directory / filename).write_text("private\n", encoding="utf-8")
                link = source / f"link-{directory.replace('.', 'dot')}"
                try:
                    os.symlink(f"{directory}/{filename}", link)
                except OSError as exc:
                    self.skipTest(f"fixture symlink creation unavailable: {exc}")
                with self.assertRaisesRegex(ValueError, "excluded metadata"):
                    materialize_candidate.materialize(
                        source,
                        root / f"candidate-{directory.replace('.', 'dot')}",
                        [materialize_candidate.normalize_relative(link.name)],
                    )

    def test_copy_entry_rejects_directory_alias_identity_outside_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            outside = root / "outside"
            destination = root / "candidate"
            source.mkdir()
            outside.mkdir()
            destination.mkdir()
            (outside / "private.txt").write_text("outside\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "filesystem alias escapes"):
                materialize_candidate.copy_entry(
                    source.resolve(), destination, outside,
                    destination / "linked", [], frozenset(),
                )

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_rejects_escaping_intermediate_symlink(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            outside = root / "outside"
            outside.mkdir()
            (outside / "private.txt").write_text("outside\n", encoding="utf-8")
            try:
                os.symlink(outside, source / "linked")
            except OSError as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            with self.assertRaisesRegex(ValueError, "intermediate symlink escapes"):
                materialize_candidate.materialize(
                    source,
                    root / "candidate",
                    [materialize_candidate.normalize_relative("linked/private.txt")],
                )

    def test_cli_reports_missing_allowlisted_path_without_leaving_candidate(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            destination = root / "candidate"
            allowlist = root / "allowlist.json"
            allowlist.write_text(json.dumps(["missing.txt"]), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), str(source), str(destination), str(allowlist)],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
