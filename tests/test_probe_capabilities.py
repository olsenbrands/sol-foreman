import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "skills/sol-foreman/scripts/probe_capabilities.py"
sys.path.insert(0, str(SCRIPT.parent))
import probe_capabilities  # noqa: E402


class ProbeCapabilitiesTests(unittest.TestCase):
    def assert_no_sensitive_output(self, payload, sensitive_fields, sensitive_values):
        rendered_json = json.dumps(payload, sort_keys=True)
        text_output = io.StringIO()
        with contextlib.redirect_stdout(text_output):
            probe_capabilities.print_text(payload)

        for secret in (*sensitive_fields, *sensitive_values):
            self.assertNotIn(secret, rendered_json)
            self.assertNotIn(secret, text_output.getvalue())

    def test_t3_vc1_claude_auth_sanitizes_account_fields(self):
        sensitive_fields = ("email", "organizationName", "organizationUuid", "accountId")
        sensitive_values = (
            "person@example.invalid",
            "Example Organization",
            "org-1234-private",
            "acct-5678-private",
        )
        raw_auth = json.dumps(
            {
                "loggedIn": True,
                "authMethod": "claude.ai",
                "apiProvider": "firstParty",
                "subscriptionType": "max",
                "email": sensitive_values[0],
                "organizationName": sensitive_values[1],
                "organizationUuid": sensitive_values[2],
                "accountId": sensitive_values[3],
                "unrelated": {"privateToken": "do-not-return"},
            }
        )

        with patch.object(probe_capabilities, "run", return_value=(0, raw_auth)):
            safe = probe_capabilities.claude_auth("claude")

        self.assertEqual(
            set(safe),
            {"checked", "logged_in", "method", "provider", "subscription_type"},
        )
        self.assertEqual(
            {safe["method"], safe["provider"], safe["subscription_type"]},
            {"claude.ai", "first-party", "max"},
        )
        payload = {
            "native_codex": {"status": "inspect-current-runtime", "note": "safe"},
            "codex_cli": {"available": False},
            "claude_cli": {"available": True, "version": "unknown", "auth": safe},
            "warnings": [],
        }
        self.assert_no_sensitive_output(payload, sensitive_fields, sensitive_values)

    def test_t3_vc2_non_json_and_failed_auth_do_not_echo_raw_output(self):
        sensitive_fields = ("email", "organizationUuid", "statusDetail")
        sensitive_values = (
            "person@example.invalid",
            "org-9999-private",
            "AUTH-FAILURE-DETAIL-PRIVATE",
        )
        raw_status = (
            "Authentication failed: email="
            + sensitive_values[0]
            + " organizationUuid="
            + sensitive_values[1]
            + " statusDetail="
            + sensitive_values[2]
        )

        with patch.object(probe_capabilities, "run", return_value=(0, raw_status)):
            non_json = probe_capabilities.claude_auth("claude")
        self.assertEqual(non_json, {"checked": True, "logged_in": False, "method": "unknown"})
        self.assert_no_sensitive_output(
            {
                "native_codex": {"status": "inspect-current-runtime", "note": "safe"},
                "codex_cli": {"available": False},
                "claude_cli": {"available": True, "auth": non_json},
                "warnings": [],
            },
            sensitive_fields,
            sensitive_values,
        )

        with patch.object(probe_capabilities, "run", return_value=(1, raw_status)):
            failed = probe_capabilities.claude_auth("claude")
        self.assertEqual(
            failed,
            {
                "checked": True,
                "logged_in": False,
                "method": "unknown",
                "error": "auth status command failed",
            },
        )
        self.assert_no_sensitive_output(
            {
                "native_codex": {"status": "inspect-current-runtime", "note": "safe"},
                "codex_cli": {"available": False},
                "claude_cli": {"available": True, "auth": failed},
                "warnings": [],
            },
            sensitive_fields,
            sensitive_values,
        )

    def test_t3_vc3_codex_auth_classifies_without_returning_status(self):
        raw_status = (
            "AUTH-STATUS-PRIVATE: logged in with ChatGPT; "
            "email=person@example.invalid"
        )
        with patch.object(probe_capabilities, "run", return_value=(0, raw_status)):
            safe = probe_capabilities.codex_auth("codex")

        self.assertEqual(
            safe,
            {"checked": True, "logged_in": True, "method": "chatgpt"},
        )
        rendered = json.dumps(safe)
        self.assertNotIn(raw_status, rendered)
        self.assertNotIn("AUTH-STATUS-PRIVATE", rendered)
        self.assertNotIn("email", rendered)
        self.assertNotIn("person@example.invalid", rendered)

    def test_t3_vc4_probe_runs_from_unrelated_directory_without_model_calls(self):
        with tempfile.TemporaryDirectory() as unrelated, tempfile.TemporaryDirectory() as codex_home:
            environment = os.environ.copy()
            environment["CODEX_HOME"] = codex_home
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "--json", "--no-auth"],
                cwd=unrelated,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertFalse(payload["billable_model_calls_made"])

    def test_t3_vc5_model_cache_and_newer_generation_detection(self):
        with tempfile.TemporaryDirectory() as codex_home:
            cache_path = Path(codex_home) / "models_cache.json"
            cache_path.write_text(
                json.dumps(
                    {
                        "fetched_at": "2026-07-18T00:00:00Z",
                        "client_version": "1.2.3",
                        "models": [
                            {
                                "slug": "gpt-5.6-codex",
                                "display_name": "Codex 5.6",
                                "description": "bundled",
                                "default_reasoning_level": "high",
                                "supported_reasoning_levels": [
                                    {"effort": "low"},
                                    {"effort": "high"},
                                ],
                            },
                            {
                                "slug": "gpt-5.7-codex",
                                "display_name": "Codex 5.7",
                                "description": "newer",
                                "default_reasoning_level": "medium",
                                "supported_reasoning_levels": [{"effort": "medium"}],
                            },
                            {"display_name": "ignored without slug"},
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = probe_capabilities.read_codex_models(Path(codex_home))

        self.assertEqual(probe_capabilities.parse_generation("gpt-5.6-codex"), (5, 6))
        self.assertIsNone(probe_capabilities.parse_generation("claude-opus-4-8"))
        self.assertEqual([model["slug"] for model in result["models"]], ["gpt-5.6-codex", "gpt-5.7-codex"])
        self.assertEqual(result["models"][0]["supported_efforts"], ["low", "high"])
        self.assertEqual(result["newer_than_bundled_snapshot"], ["gpt-5.7-codex"])
        self.assertEqual(
            result["unfamiliar_to_bundled_snapshot"],
            ["gpt-5.6-codex", "gpt-5.7-codex"],
        )

    def test_t3_vc6_bundled_models_are_not_marked_unfamiliar(self):
        with tempfile.TemporaryDirectory() as codex_home:
            cache_path = Path(codex_home) / "models_cache.json"
            cache_path.write_text(
                json.dumps(
                    {
                        "fetched_at": "2026-07-18T00:00:00Z",
                        "models": [
                            {"slug": slug, "supported_reasoning_levels": []}
                            for slug in sorted(probe_capabilities.BUNDLED_CODEX_MODEL_SLUGS)
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = probe_capabilities.read_codex_models(Path(codex_home))

        self.assertEqual(result["unfamiliar_to_bundled_snapshot"], [])

    def test_t3_vc7_unfamiliar_cache_entry_emits_refresh_warning(self):
        with tempfile.TemporaryDirectory() as codex_home:
            cache_path = Path(codex_home) / "models_cache.json"
            cache_path.write_text(
                json.dumps(
                    {
                        "fetched_at": "2026-07-18T00:00:00Z",
                        "models": [
                            {
                                "slug": "gpt-experimental-seat",
                                "supported_reasoning_levels": [],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            which = lambda name: "/usr/local/bin/codex" if name == "codex" else None
            with patch.dict(os.environ, {"CODEX_HOME": codex_home}), \
                patch.object(probe_capabilities.shutil, "which", side_effect=which), \
                patch.object(probe_capabilities, "version", return_value="codex-cli test"):
                result = probe_capabilities.collect(check_auth=False)

        self.assertIn(
            "The Codex cache contains a model absent from the bundled 2026-07-18 snapshot; research it in current official sources before routing.",
            result["warnings"],
        )

    def test_t3_vc8_malformed_cache_shapes_degrade_without_crashing(self):
        with tempfile.TemporaryDirectory() as codex_home:
            cache_path = Path(codex_home) / "models_cache.json"
            cache_path.write_text(json.dumps(["not", "an", "object"]), encoding="utf-8")
            top_level = probe_capabilities.read_codex_models(Path(codex_home))

            cache_path.write_text(json.dumps({"models": "not-a-list"}), encoding="utf-8")
            non_list_models = probe_capabilities.read_codex_models(Path(codex_home))

            cache_path.write_text(
                json.dumps(
                    {
                        "fetched_at": "2026-07-18T00:00:00Z",
                        "models": [
                            "not-an-object",
                            {"slug": 56, "supported_reasoning_levels": []},
                            {"slug": "", "supported_reasoning_levels": []},
                            {
                                "slug": "gpt-" + ("9" * 5_000) + ".6-sol",
                                "supported_reasoning_levels": [],
                            },
                            {
                                "slug": "gpt-experimental-seat",
                                "supported_reasoning_levels": [
                                    "not-an-object",
                                    {"effort": 3},
                                    {"effort": "high"},
                                ],
                            },
                            {
                                "slug": "gpt-non-list-efforts",
                                "supported_reasoning_levels": "not-a-list",
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            mixed_entries = probe_capabilities.read_codex_models(Path(codex_home))

            cache_path.write_bytes(b"\xff\xfe\xfd")
            invalid_utf8 = probe_capabilities.read_codex_models(Path(codex_home))

            cache_path.write_text("{}", encoding="utf-8")
            with patch.object(probe_capabilities.json, "loads", side_effect=RecursionError):
                recursive_json = probe_capabilities.read_codex_models(Path(codex_home))

        self.assertEqual(top_level["error"], "unexpected models_cache.json shape")
        self.assertEqual(non_list_models["error"], "unexpected models_cache.json shape")
        self.assertEqual(invalid_utf8["error"], "could not parse models_cache.json")
        self.assertEqual(recursive_json["error"], "could not parse models_cache.json")
        self.assertIsNone(probe_capabilities.parse_generation("gpt-" + ("9" * 5_000) + ".6-sol"))
        self.assertEqual(
            mixed_entries["models"],
            [
                {
                    "slug": "gpt-experimental-seat",
                    "default_effort": None,
                    "supported_efforts": ["high"],
                },
                {
                    "slug": "gpt-non-list-efforts",
                    "default_effort": None,
                    "supported_efforts": [],
                },
            ],
        )
        text_output = io.StringIO()
        with contextlib.redirect_stdout(text_output):
            probe_capabilities.print_text(
                {
                    "native_codex": {"status": "inspect-current-runtime", "note": "safe"},
                    "codex_cli": {
                        "available": True,
                        "version": "test",
                        "model_cache": mixed_entries,
                    },
                    "claude_cli": {"available": False},
                    "warnings": [],
                }
            )
        self.assertIn("efforts=high", text_output.getvalue())

    def test_t3_vc9_config_and_cache_expose_only_allowlisted_values(self):
        with tempfile.TemporaryDirectory() as codex_home:
            root = Path(codex_home)
            (root / "config.toml").write_text(
                'model = "person@example.invalid"\nmodel_reasoning_effort = "TOKEN-private"\nservice_tier = "secret"\n',
                encoding="utf-8",
            )
            (root / "models_cache.json").write_text(
                json.dumps(
                    {
                        "fetched_at": "2026-07-18T00:00:00Z",
                        "client_version": "person@example.invalid",
                        "models": [
                            {
                                "slug": "person@example.invalid",
                                "display_name": "TOKEN-private",
                                "description": "do not expose",
                                "default_reasoning_level": "private",
                                "supported_reasoning_levels": [{"effort": "high"}],
                            },
                            {
                                "slug": "gpt-safe-model",
                                "display_name": "TOKEN-private",
                                "description": "do not expose",
                                "default_reasoning_level": "high",
                                "supported_reasoning_levels": [{"effort": "high"}],
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            preferences = probe_capabilities.read_codex_preferences(root)
            cache = probe_capabilities.read_codex_models(root)
        rendered = json.dumps({"preferences": preferences, "cache": cache})
        self.assertNotIn(str(root), rendered)
        self.assertNotIn("person@example.invalid", rendered)
        self.assertNotIn("TOKEN-private", rendered)
        self.assertNotIn("do not expose", rendered)
        self.assertEqual(cache["models"][0]["slug"], "gpt-safe-model")

    def test_t3_vc10_missing_tomllib_degrades_without_crash(self):
        with tempfile.TemporaryDirectory() as codex_home:
            root = Path(codex_home)
            (root / "config.toml").write_text('model = "gpt-5.6-sol"\n', encoding="utf-8")
            with patch.dict(sys.modules, {"tomllib": None}):
                result = probe_capabilities.read_codex_preferences(root)
        self.assertEqual(result, {"exists": True, "error": "could not parse config.toml"})

    def test_t3_vc11_invalid_and_future_cache_timestamps_emit_refresh_warning(self):
        cases = (
            (None, "Codex model cache timestamp is missing or invalid; refresh before asserting current availability."),
            ("not-a-timestamp", "Codex model cache timestamp is missing or invalid; refresh before asserting current availability."),
            (
                (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
                "Codex model cache timestamp is in the future; refresh before asserting current availability.",
            ),
            ("2999-01-01T00:00:00Z", "Codex model cache timestamp is in the future; refresh before asserting current availability."),
            ("2000-01-01T00:00:00Z", "Codex model cache is older than seven days; refresh before asserting current availability."),
        )
        for fetched_at, expected_warning in cases:
            with self.subTest(fetched_at=fetched_at), tempfile.TemporaryDirectory() as codex_home:
                cache_path = Path(codex_home) / "models_cache.json"
                cache_path.write_text(
                    json.dumps({"fetched_at": fetched_at, "models": []}),
                    encoding="utf-8",
                )
                which = lambda name: "/usr/local/bin/codex" if name == "codex" else None
                with patch.dict(os.environ, {"CODEX_HOME": codex_home}), \
                    patch.object(probe_capabilities.shutil, "which", side_effect=which), \
                    patch.object(probe_capabilities, "version", return_value="codex-cli test"):
                    result = probe_capabilities.collect(check_auth=False)

                self.assertIn(expected_warning, result["warnings"])


if __name__ == "__main__":
    unittest.main()
