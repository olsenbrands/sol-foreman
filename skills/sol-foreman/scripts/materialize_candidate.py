#!/usr/bin/env python3
"""Copy an explicit product-path allowlist into an isolated verifier candidate."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import sys
from pathlib import Path, PurePosixPath
from typing import Any

import path_policy


DEFAULT_EXCLUDES = path_policy.EXCLUDED_COMPONENTS


def normalize_relative(value: Any) -> PurePosixPath:
    return path_policy.normalize_repo_path(value, allow_globs=False)


def load_allowlist(path: Path) -> list[PurePosixPath]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list) or not payload:
        raise ValueError("allowlist must be a non-empty JSON array")
    normalized = [normalize_relative(item) for item in payload]
    canonical = [tuple(part.casefold() for part in item.parts) for item in normalized]
    if len(canonical) != len(set(canonical)):
        raise ValueError("allowlist contains case-alias duplicate paths")
    paths = sorted(normalized, key=lambda item: tuple(part.casefold() for part in item.parts))
    for index, item in enumerate(paths):
        item_parts = tuple(part.casefold() for part in item.parts)
        for other in paths[:index]:
            other_parts = tuple(part.casefold() for part in other.parts)
            if item_parts[: len(other_parts)] == other_parts:
                raise ValueError(f"overlapping allowlist entries: {other} and {item}")
    return paths


def safe_symlink(
    source_root: Path,
    destination_root: Path,
    source: Path,
    destination: Path,
    transformations: list[dict[str, str]],
    stack: frozenset[Path],
) -> None:
    target = os.readlink(source)
    target_path = Path(target)
    if target_path.is_absolute():
        raise ValueError(f"absolute symlink is not allowed: {source}")
    resolved = (source.parent / target_path).resolve(strict=False)
    try:
        resolved.relative_to(source_root)
    except ValueError as exc:
        raise ValueError(f"escaping symlink is not allowed: {source}") from exc
    resolved = resolved.resolve(strict=True)
    relative_target = PurePosixPath(resolved.relative_to(source_root).as_posix())
    if path_policy.contains_excluded_component(relative_target):
        raise ValueError(f"symlink target enters excluded metadata or cache content: {source}")
    if resolved in stack:
        raise ValueError(f"symlink dereference cycle is not allowed: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    transformations.append(
        {
            "path": destination.relative_to(destination_root).as_posix(),
            "action": "dereferenced-internal-symlink",
            "target": target,
        }
    )
    copy_entry(
        source_root,
        destination_root,
        resolved,
        destination,
        transformations,
        stack,
    )


def copy_entry(
    source_root: Path,
    destination_root: Path,
    source: Path,
    destination: Path,
    transformations: list[dict[str, str]],
    stack: frozenset[Path],
) -> None:
    metadata = source.lstat()
    if stat.S_ISLNK(metadata.st_mode):
        safe_symlink(
            source_root, destination_root, source, destination, transformations, stack
        )
        return
    resolved_source = source.resolve(strict=True)
    try:
        resolved_relative = PurePosixPath(resolved_source.relative_to(source_root).as_posix())
    except ValueError as exc:
        raise ValueError(f"filesystem alias escapes source: {source}") from exc
    if path_policy.contains_excluded_component(resolved_relative):
        raise ValueError(f"filesystem alias enters excluded metadata or cache content: {source}")
    if stat.S_ISREG(metadata.st_mode):
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        destination.chmod(stat.S_IMODE(metadata.st_mode) & 0o777)
        return
    if not stat.S_ISDIR(metadata.st_mode):
        raise ValueError(f"special filesystem entry is not allowed: {source}")
    identity = resolved_source
    if identity in stack:
        raise ValueError(f"directory cycle is not allowed: {source}")
    destination.mkdir(parents=True, exist_ok=False)
    for child in sorted(source.iterdir(), key=lambda item: item.name):
        if child.name.casefold() in DEFAULT_EXCLUDES or child.suffix.casefold() == ".pyc":
            continue
        copy_entry(
            source_root,
            destination_root,
            child,
            destination / child.name,
            transformations,
            stack | {identity},
        )


def materialize(source: Path, destination: Path, allowlist: list[PurePosixPath]) -> dict[str, Any]:
    source = source.resolve(strict=True)
    if not source.is_dir():
        raise ValueError("source must be a directory")
    destination = destination.resolve(strict=False)
    try:
        destination.relative_to(source)
    except ValueError:
        pass
    else:
        raise ValueError("destination must not be inside source")
    if destination.exists():
        raise ValueError("destination must not already exist")
    destination.mkdir(parents=True)

    copied: list[str] = []
    transformations: list[dict[str, str]] = []
    try:
        for relative in allowlist:
            source_item = source.joinpath(*relative.parts)
            if not source_item.exists() and not source_item.is_symlink():
                raise ValueError(f"allowlisted path does not exist: {relative}")
            resolved_parent = source_item.parent.resolve(strict=True)
            try:
                resolved_parent.relative_to(source)
            except ValueError as exc:
                raise ValueError(f"intermediate symlink escapes source: {relative}") from exc
            relative_parent = PurePosixPath(resolved_parent.relative_to(source).as_posix())
            if path_policy.contains_excluded_component(relative_parent):
                raise ValueError(f"intermediate path enters excluded metadata or cache content: {relative}")
            source_item = resolved_parent / source_item.name
            copy_entry(
                source,
                destination,
                source_item,
                destination.joinpath(*relative.parts),
                transformations,
                frozenset(),
            )
            copied.append(relative.as_posix())
    except Exception:
        shutil.rmtree(destination, ignore_errors=True)
        raise
    return {
        "schema_version": 1,
        "source": str(source),
        "destination": str(destination),
        "copied": copied,
        "transformations": transformations,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("allowlist", type=Path, help="JSON array of relative product paths")
    args = parser.parse_args()
    try:
        result = materialize(args.source, args.destination, load_allowlist(args.allowlist))
    except (OSError, ValueError, RecursionError) as exc:
        print(f"candidate materialization failed: {exc}", file=sys.stderr)
        return 1
    json.dump(result, sys.stdout, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
