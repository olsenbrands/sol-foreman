#!/usr/bin/env python3
"""Create a deterministic, privacy-local fingerprint of a directory tree."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
from pathlib import Path
from typing import Any, Iterator


SCHEMA_VERSION = 1
DEFAULT_EXCLUDES = (".git",)


def normalize_exclude(value: str) -> str:
    normalized = value.replace("\\", "/").strip("/")
    if not normalized or normalized in {".", ".."} or normalized.startswith("../"):
        raise ValueError(f"invalid relative exclude: {value!r}")
    return normalized


def is_excluded(relative: str, excludes: tuple[str, ...]) -> bool:
    return any(relative == item or relative.startswith(f"{item}/") for item in excludes)


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def entry_record(path: Path, relative: str) -> dict[str, Any]:
    metadata = path.lstat()
    mode = f"{stat.S_IMODE(metadata.st_mode):04o}"
    record: dict[str, Any] = {"path": relative, "mode": mode}
    if stat.S_ISDIR(metadata.st_mode):
        record["type"] = "directory"
    elif stat.S_ISREG(metadata.st_mode):
        record.update(type="file", size=metadata.st_size, sha256=hash_file(path))
    elif stat.S_ISLNK(metadata.st_mode):
        record.update(type="symlink", target=os.readlink(path))
    else:
        record.update(type="special", device=metadata.st_rdev)
    return record


def walk(root: Path, excludes: tuple[str, ...]) -> Iterator[dict[str, Any]]:
    def visit(directory: Path, prefix: str = "") -> Iterator[dict[str, Any]]:
        with os.scandir(directory) as scan:
            entries = sorted(scan, key=lambda item: item.name)
        for item in entries:
            relative = f"{prefix}/{item.name}" if prefix else item.name
            relative = relative.replace(os.sep, "/")
            if is_excluded(relative, excludes):
                continue
            path = Path(item.path)
            record = entry_record(path, relative)
            yield record
            if record["type"] == "directory":
                yield from visit(path, relative)

    yield from visit(root)


def fingerprint(root: Path, excludes: tuple[str, ...], include_manifest: bool) -> dict[str, Any]:
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError(f"root is not a directory: {root}")
    records = list(walk(root, excludes))
    digest = hashlib.sha256()
    for record in records:
        canonical = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        digest.update(canonical.encode("utf-8"))
        digest.update(b"\n")
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": "sha256",
        "digest": digest.hexdigest(),
        "entry_count": len(records),
        "excluded": list(excludes),
    }
    if include_manifest:
        result["entries"] = records
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="directory to fingerprint")
    parser.add_argument("--exclude", action="append", default=[], help="additional relative path to exclude")
    parser.add_argument("--manifest", action="store_true", help="include the canonical entry manifest")
    args = parser.parse_args()
    try:
        excludes = tuple(dict.fromkeys((*DEFAULT_EXCLUDES, *(normalize_exclude(item) for item in args.exclude))))
        payload = fingerprint(args.root, excludes, args.manifest)
    except (OSError, ValueError) as exc:
        print(f"fingerprint failed: {exc}", file=sys.stderr)
        return 1
    json.dump(payload, sys.stdout, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
