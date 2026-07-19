#!/usr/bin/env python3
"""Inspect local Codex/Claude orchestration capabilities without model calls."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CURRENT_CODEX_GENERATION = (5, 6)
MAX_MODEL_SLUG_LENGTH = 128
BUNDLED_CODEX_MODEL_SLUGS = frozenset(
    {
        "gpt-5.6-sol",
        "gpt-5.6-terra",
        "gpt-5.6-luna",
        "gpt-5.5",
        "gpt-5.4",
        "gpt-5.4-mini",
        "gpt-5.3-codex-spark",
        "codex-auto-review",
    }
)


def safe_category(value: Any, aliases: dict[str, str]) -> str:
    """Return a known category without exposing arbitrary provider output."""
    if not isinstance(value, str):
        return "unknown"
    normalized = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return aliases.get(normalized, "unknown")


def run(command: list[str], timeout: int = 10) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, str(exc)
    output = (completed.stdout or completed.stderr or "").strip()
    return completed.returncode, output


def codex_auth(executable: str) -> dict[str, Any]:
    code, output = run([executable, "login", "status"])
    lowered = output.lower()
    method = "unknown"
    if "chatgpt" in lowered:
        method = "chatgpt"
    elif "api key" in lowered or "api_key" in lowered:
        method = "api-key"
    return {
        "checked": True,
        "logged_in": code == 0 and ("logged in" in lowered or "authenticated" in lowered),
        "method": method,
    }


def claude_auth(executable: str) -> dict[str, Any]:
    code, output = run([executable, "auth", "status"])
    safe: dict[str, Any] = {"checked": True, "logged_in": False, "method": "unknown"}
    if code != 0:
        safe["error"] = "auth status command failed"
        return safe
    try:
        payload = json.loads(output)
    except json.JSONDecodeError:
        lowered = output.lower()
        safe["logged_in"] = "logged in" in lowered or "authenticated" in lowered
        return safe
    if not isinstance(payload, dict):
        safe["error"] = "auth status response was not an object"
        return safe
    safe["logged_in"] = bool(payload.get("loggedIn"))
    safe["method"] = safe_category(
        payload.get("authMethod"),
        {
            "oauth": "oauth",
            "api-key": "api-key",
            "api-key-auth": "api-key",
            "chatgpt": "chatgpt",
            "claude-ai": "claude.ai",
        },
    )
    safe["provider"] = safe_category(
        payload.get("apiProvider"),
        {
            "anthropic": "anthropic",
            "first-party": "first-party",
            "firstparty": "first-party",
            "bedrock": "bedrock",
            "vertex": "vertex",
        },
    )
    safe["subscription_type"] = safe_category(
        payload.get("subscriptionType"),
        {
            "free": "free",
            "pro": "pro",
            "max": "max",
            "team": "team",
            "enterprise": "enterprise",
        },
    )
    return safe


def read_codex_preferences(codex_home: Path) -> dict[str, Any]:
    config_path = codex_home / "config.toml"
    result: dict[str, Any] = {"path": str(config_path), "exists": config_path.is_file()}
    if not config_path.is_file():
        return result
    try:
        import tomllib

        with config_path.open("rb") as handle:
            payload = tomllib.load(handle)
        for key in ("model", "model_reasoning_effort", "service_tier"):
            if key in payload:
                result[key] = payload[key]
    except (OSError, ValueError):
        result["error"] = "could not parse config.toml"
    return result


def parse_generation(slug: str) -> tuple[int, int] | None:
    match = re.match(r"^gpt-(\d+)\.(\d+)", slug)
    if not match:
        return None
    try:
        return int(match.group(1)), int(match.group(2))
    except ValueError:
        return None


def cache_age_days(value: Any) -> float | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - parsed).total_seconds() / 86400
    except ValueError:
        return None


def read_codex_models(codex_home: Path) -> dict[str, Any]:
    cache_path = codex_home / "models_cache.json"
    result: dict[str, Any] = {"path": str(cache_path), "exists": cache_path.is_file()}
    if not cache_path.is_file():
        return result
    try:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, RecursionError):
        result["error"] = "could not parse models_cache.json"
        return result

    if not isinstance(payload, dict):
        result["error"] = "unexpected models_cache.json shape"
        return result

    raw_models = payload.get("models", [])
    if not isinstance(raw_models, list):
        result["error"] = "unexpected models_cache.json shape"
        return result

    fetched_at = payload.get("fetched_at")
    result["fetched_at"] = fetched_at if isinstance(fetched_at, str) else None
    result["age_days"] = cache_age_days(fetched_at)
    result["client_version"] = payload.get("client_version")
    models: list[dict[str, Any]] = []
    newer: list[str] = []
    unfamiliar: list[str] = []
    for item in raw_models:
        if not isinstance(item, dict):
            continue
        slug = item.get("slug")
        if (
            not isinstance(slug, str)
            or not slug
            or len(slug) > MAX_MODEL_SLUG_LENGTH
        ):
            continue
        raw_efforts = item.get("supported_reasoning_levels", [])
        if not isinstance(raw_efforts, list):
            raw_efforts = []
        efforts = [
            effort.get("effort")
            for effort in raw_efforts
            if (
                isinstance(effort, dict)
                and isinstance(effort.get("effort"), str)
                and effort.get("effort")
            )
        ]
        models.append(
            {
                "slug": slug,
                "display_name": item.get("display_name"),
                "description": item.get("description"),
                "default_effort": item.get("default_reasoning_level"),
                "supported_efforts": efforts,
            }
        )
        generation = parse_generation(slug)
        if generation and generation > CURRENT_CODEX_GENERATION:
            newer.append(slug)
        if slug not in BUNDLED_CODEX_MODEL_SLUGS:
            unfamiliar.append(slug)
    result["models"] = models
    result["newer_than_bundled_snapshot"] = newer
    result["unfamiliar_to_bundled_snapshot"] = unfamiliar
    return result


def version(executable: str) -> str:
    code, output = run([executable, "--version"])
    return output if code == 0 else "unknown"


def collect(check_auth: bool) -> dict[str, Any]:
    codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()
    codex = shutil.which("codex")
    claude = shutil.which("claude")
    result: dict[str, Any] = {
        "schema_version": 1,
        "billable_model_calls_made": False,
        "native_codex": {
            "status": "inspect-current-runtime",
            "note": "Check the active collaboration tool schema and thread cap; this script cannot see in-session tools.",
        },
        "codex_cli": {"available": bool(codex)},
        "claude_cli": {"available": bool(claude)},
        "warnings": [],
    }

    if codex:
        result["codex_cli"].update(
            {
                "path": codex,
                "version": version(codex),
                "preferences": read_codex_preferences(codex_home),
                "model_cache": read_codex_models(codex_home),
            }
        )
        if check_auth:
            result["codex_cli"]["auth"] = codex_auth(codex)
        model_cache = result["codex_cli"]["model_cache"]
        if not model_cache.get("exists"):
            result["warnings"].append("Codex model cache is missing; use current official docs and a consented tiny probe.")
        else:
            if model_cache.get("error"):
                result["warnings"].append("Codex model cache has an unexpected or unreadable shape; refresh before asserting current availability.")
            if model_cache.get("newer_than_bundled_snapshot"):
                result["warnings"].append("A newer Codex generation than the bundled 2026-07-18 snapshot is present; refresh routing guidance.")
            if model_cache.get("unfamiliar_to_bundled_snapshot"):
                result["warnings"].append("The Codex cache contains a model absent from the bundled 2026-07-18 snapshot; research it in current official sources before routing.")
            age_days = model_cache.get("age_days")
            if not model_cache.get("error") and age_days is None:
                result["warnings"].append("Codex model cache timestamp is missing or invalid; refresh before asserting current availability.")
            elif isinstance(age_days, (int, float)) and age_days < 0:
                result["warnings"].append("Codex model cache timestamp is in the future; refresh before asserting current availability.")
            elif isinstance(age_days, (int, float)) and age_days > 7:
                result["warnings"].append("Codex model cache is older than seven days; refresh before asserting current availability.")

    if claude:
        result["claude_cli"].update({"path": claude, "version": version(claude)})
        if check_auth:
            result["claude_cli"]["auth"] = claude_auth(claude)

    if not codex and not claude:
        result["warnings"].append("No external CLI lane found; use native Codex collaboration or solo discipline.")
    return result


def print_text(payload: dict[str, Any]) -> None:
    print("Sol Foreman capability probe (no model calls)")
    native = payload["native_codex"]
    print(f"Native Codex: {native['status']} — {native['note']}")
    for key, label in (("codex_cli", "Codex CLI"), ("claude_cli", "Claude CLI")):
        lane = payload[key]
        if not lane.get("available"):
            print(f"{label}: unavailable")
            continue
        print(f"{label}: available | {lane.get('version', 'unknown')}")
        auth = lane.get("auth")
        if auth:
            print(
                f"  auth: logged_in={auth.get('logged_in')} "
                f"method={auth.get('method', 'unknown')}"
            )
        if key == "codex_cli":
            preferences = lane.get("preferences", {})
            print(
                f"  configured: model={preferences.get('model', 'unset')} "
                f"effort={preferences.get('model_reasoning_effort', 'unset')}"
            )
            models = lane.get("model_cache", {}).get("models", [])
            if models:
                print("  cached models:")
                for model in models:
                    efforts = ",".join(model.get("supported_efforts", []))
                    print(
                        f"    - {model['slug']} | default={model.get('default_effort')} "
                        f"| efforts={efforts}"
                    )
    for warning in payload.get("warnings", []):
        print(f"WARNING: {warning}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect Codex and Claude orchestration capabilities without billable model calls."
    )
    parser.add_argument("--json", action="store_true", help="emit structured JSON")
    parser.add_argument(
        "--no-auth",
        action="store_true",
        help="skip non-billable CLI authentication-status checks",
    )
    args = parser.parse_args()
    payload = collect(check_auth=not args.no_auth)
    if args.json:
        json.dump(payload, sys.stdout, indent=2, sort_keys=True)
        print()
    else:
        print_text(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
