#!/usr/bin/env python3
"""Validate a Sol Foreman ticket before an implementation dispatch."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

import path_policy


SCHEMA_VERSION = 1
EXECUTION_KINDS = frozenset({"implementation", "integration", "docs"})
KNOWN_KINDS = EXECUTION_KINDS | {"recon", "verification"}


def nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def string_list(payload: dict[str, Any], key: str, errors: list[str]) -> list[str]:
    value = payload.get(key)
    if not isinstance(value, list) or any(not nonempty_string(item) for item in value):
        errors.append(f"{key} must be a list of non-empty strings")
        return []
    return [item.strip() for item in value]


def criteria_list(payload: dict[str, Any], errors: list[str]) -> list[dict[str, str]]:
    value = payload.get("criteria")
    if not isinstance(value, list) or not value:
        errors.append("criteria must be a non-empty list of {id, promise} objects")
        return []
    result: list[dict[str, str]] = []
    identifiers: set[str] = set()
    for item in value:
        if not isinstance(item, dict):
            errors.append("each criterion must be an object")
            continue
        identifier = item.get("id")
        promise = item.get("promise")
        if not isinstance(identifier, str) or not re.fullmatch(r"[A-Z][A-Z0-9-]{1,31}", identifier):
            errors.append("criterion ids must be 2-32 uppercase letters, digits, or hyphens")
            continue
        if identifier in identifiers:
            errors.append(f"duplicate criterion id: {identifier}")
            continue
        if not nonempty_string(promise) or len(promise.strip()) < 10:
            errors.append(f"criterion {identifier} promise must contain at least 10 characters")
            continue
        identifiers.add(identifier)
        result.append({"id": identifier, "promise": promise.strip()})
    return result


def gate_list(
    payload: dict[str, Any], criterion_ids: set[str], errors: list[str]
) -> list[dict[str, str]]:
    value = payload.get("verification_gates")
    if not isinstance(value, list) or not value:
        errors.append("verification_gates must be a non-empty list of structured gate objects")
        return []
    result: list[dict[str, str]] = []
    covered: set[str] = set()
    for item in value:
        if not isinstance(item, dict):
            errors.append("each verification gate must be an object")
            continue
        criterion_id = item.get("criterion_id")
        procedure = item.get("procedure")
        expected = item.get("expected")
        if criterion_id not in criterion_ids:
            errors.append(f"verification gate references unknown criterion: {criterion_id!r}")
            continue
        if not nonempty_string(procedure) or len(procedure.strip()) < 8:
            errors.append(f"gate for {criterion_id} requires a specific procedure")
            continue
        if not nonempty_string(expected) or len(expected.strip()) < 8:
            errors.append(f"gate for {criterion_id} requires an expected observation")
            continue
        covered.add(criterion_id)
        result.append(
            {
                "criterion_id": criterion_id,
                "procedure": procedure.strip(),
                "expected": expected.strip(),
            }
        )
    missing = criterion_ids - covered
    if missing:
        errors.append(f"criteria missing verification gates: {', '.join(sorted(missing))}")
    return result


def validate_expected_paths(paths: list[str], errors: list[str]) -> None:
    for value in paths:
        try:
            path_policy.normalize_repo_path(value, allow_globs=True)
        except ValueError as exc:
            errors.append(f"invalid expected path {value!r}: {exc}")


def validate_atomic_labels(values: list[str], key: str, errors: list[str]) -> None:
    for value in values:
        if re.search(r"\s(?:\+|&|and)\s|[,;]", value, flags=re.IGNORECASE):
            errors.append(f"split compound {key} entry into separate values: {value!r}")


def positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def validate_checkpoint(
    payload: dict[str, Any], required: bool, estimated_minutes: int, errors: list[str]
) -> None:
    checkpoint = payload.get("first_checkpoint")
    if checkpoint is None and not required:
        return
    if not isinstance(checkpoint, dict):
        errors.append("first_checkpoint must be an object")
        return
    minutes = checkpoint.get("minutes")
    if not positive_int(minutes):
        errors.append("first_checkpoint.minutes must be a positive integer")
    elif estimated_minutes:
        latest = min(20, max(1, estimated_minutes // 2))
        if minutes > latest:
            errors.append(f"first_checkpoint.minutes must be no later than {latest}")
    if not nonempty_string(checkpoint.get("evidence")):
        errors.append("first_checkpoint.evidence must be a non-empty string")


def validate_override(payload: dict[str, Any], errors: list[str]) -> bool:
    override = payload.get("review_override")
    if not isinstance(override, dict):
        return False
    if override.get("approved_by_lead") is not True:
        errors.append("review_override.approved_by_lead must be true")
    for key in ("reason", "quality_case"):
        value = override.get(key)
        if not nonempty_string(value) or len(value.strip()) < 20:
            errors.append(f"review_override.{key} must contain at least 20 characters")
    return True


def evaluate(payload: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return {"schema_version": SCHEMA_VERSION, "decision": "INVALID", "reasons": ["ticket must be a JSON object"]}

    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must equal {SCHEMA_VERSION}")
    for key in ("id", "objective", "baseline"):
        if not nonempty_string(payload.get(key)):
            errors.append(f"{key} must be a non-empty string")

    kind = payload.get("kind")
    if kind not in KNOWN_KINDS:
        errors.append(f"kind must be one of: {', '.join(sorted(KNOWN_KINDS))}")

    criteria = criteria_list(payload, errors)
    gates = gate_list(payload, {item["id"] for item in criteria}, errors)
    subsystems = string_list(payload, "subsystems", errors)
    expected_paths = string_list(payload, "expected_paths", errors)
    risk_seams = string_list(payload, "risk_seams", errors)
    unknowns = string_list(payload, "material_unknowns", errors)
    dependencies = string_list(payload, "dependencies", errors)
    program_item_ids = string_list(payload, "program_item_ids", errors)

    validate_expected_paths(expected_paths, errors)
    validate_atomic_labels(subsystems, "subsystems", errors)
    validate_atomic_labels(risk_seams, "risk_seams", errors)

    if kind in EXECUTION_KINDS and not expected_paths:
        errors.append("expected_paths must contain the bounded write set for execution work")
    if kind in EXECUTION_KINDS and not program_item_ids:
        errors.append("program_item_ids must bind execution work to original program items")
    if len(program_item_ids) != len(set(program_item_ids)):
        errors.append("program_item_ids must not contain duplicates")

    estimated_minutes = payload.get("estimated_minutes")
    if not positive_int(estimated_minutes):
        errors.append("estimated_minutes must be a positive integer")
        estimated_minutes = 0

    checkpoint_required = kind in {"implementation", "integration"} and (
        bool(risk_seams) or estimated_minutes > 30
    )
    validate_checkpoint(payload, checkpoint_required, estimated_minutes, errors)

    if errors:
        return {"schema_version": SCHEMA_VERSION, "decision": "INVALID", "reasons": sorted(set(errors))}

    metrics = {
        "criteria": len(criteria),
        "subsystems": len(subsystems),
        "expected_paths": len(expected_paths),
        "risk_seams": len(risk_seams),
        "program_item_ids": len(program_item_ids),
        "estimated_minutes": estimated_minutes,
    }
    ticket_sha256 = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    if kind in EXECUTION_KINDS and (payload.get("recon_complete") is not True or unknowns):
        reasons = []
        if payload.get("recon_complete") is not True:
            reasons.append("execution work requires recon_complete=true")
        if unknowns:
            reasons.append("resolve material_unknowns in a reconnaissance ticket before dispatch")
        return {
            "schema_version": SCHEMA_VERSION,
            "decision": "RECON_REQUIRED",
            "reasons": reasons,
            "metrics": metrics,
            "ticket_sha256": ticket_sha256,
        }

    tripwires: list[str] = []
    if len(criteria) > 5:
        tripwires.append("more than 5 acceptance criteria")
    if len(subsystems) > 2:
        tripwires.append("more than 2 interacting subsystems")
    if len(expected_paths) > 10:
        tripwires.append("more than 10 expected paths")
    if len(risk_seams) > 2:
        tripwires.append("more than 2 material risk seams")
    if len(program_item_ids) > 3:
        tripwires.append("more than 3 original program items")
    if estimated_minutes > 60:
        tripwires.append("estimated duration exceeds 60 minutes")

    boundary_dimensions = sum(
        (
            len(criteria) >= 5,
            len(subsystems) >= 2,
            len(expected_paths) >= 10,
            len(risk_seams) >= 2,
            len(program_item_ids) >= 3,
            estimated_minutes >= 60,
        )
    )
    if boundary_dimensions == 2:
        tripwires.append("two ticket dimensions reach their safety boundary")

    severe = (
        len(criteria) > 8
        or len(subsystems) > 3
        or len(expected_paths) > 20
        or len(risk_seams) > 4
        or len(program_item_ids) > 6
        or estimated_minutes > 120
    )
    if severe or boundary_dimensions >= 3 or len(tripwires) >= 2:
        return {
            "schema_version": SCHEMA_VERSION,
            "decision": "DECOMPOSE_REQUIRED",
            "reasons": tripwires or ["ticket exceeds a hard size boundary"],
            "metrics": metrics,
            "ticket_sha256": ticket_sha256,
        }

    if tripwires:
        override_errors: list[str] = []
        has_override = validate_override(payload, override_errors)
        validate_checkpoint(payload, True, estimated_minutes, override_errors)
        if not has_override or override_errors:
            return {
                "schema_version": SCHEMA_VERSION,
                "decision": "REVIEW_REQUIRED",
                "reasons": tripwires + override_errors,
                "metrics": metrics,
                "ticket_sha256": ticket_sha256,
            }

    return {
        "schema_version": SCHEMA_VERSION,
        "decision": "READY",
        "reasons": tripwires,
        "override_used": bool(tripwires),
        "metrics": metrics,
        "ticket_sha256": ticket_sha256,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ticket", type=Path, help="path to the ticket JSON")
    args = parser.parse_args()
    try:
        payload = json.loads(
            args.ticket.read_text(encoding="utf-8"),
            parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"non-finite JSON value: {value}")),
        )
        result = evaluate(payload)
    except (OSError, ValueError, RecursionError) as exc:
        result = {"schema_version": SCHEMA_VERSION, "decision": "INVALID", "reasons": [f"could not read ticket: {exc}"]}
    json.dump(result, sys.stdout, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    print()
    return 0 if result["decision"] == "READY" else (1 if result["decision"] == "INVALID" else 2)


if __name__ == "__main__":
    raise SystemExit(main())
