#!/usr/bin/env python3
"""Shared cross-platform repository-path validation for Sol Foreman helpers."""

from __future__ import annotations

import re
from pathlib import Path
from pathlib import PurePosixPath
from typing import Iterable


EXCLUDED_COMPONENTS = frozenset({".git", ".foreman", "__pycache__", ".pytest_cache"})
WINDOWS_RESERVED = frozenset(
    {"con", "prn", "aux", "nul"}
    | {f"com{index}" for index in range(1, 10)}
    | {f"lpt{index}" for index in range(1, 10)}
)
GLOB_CHARACTERS = frozenset("*?[")


def _raw_parts(value: str) -> tuple[str, ...]:
    normalized = value.strip().replace("\\", "/")
    if not normalized:
        raise ValueError("path must be a non-empty string")
    if "\x00" in normalized:
        raise ValueError("path must not contain a NUL byte")
    if normalized.startswith("/") or normalized.startswith("//") or re.match(r"^[A-Za-z]:", normalized):
        raise ValueError(f"path must be repository-relative: {value!r}")
    parts = tuple(normalized.rstrip("/").split("/"))
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise ValueError(f"path must not contain empty, dot, or traversal components: {value!r}")
    return parts


def _validate_component(component: str, *, allow_globs: bool) -> None:
    folded = component.casefold()
    if folded in EXCLUDED_COMPONENTS or folded.endswith(".pyc"):
        raise ValueError(f"metadata or cache path component is forbidden: {component!r}")
    if component.endswith((" ", ".")) or ":" in component:
        raise ValueError(f"non-portable Windows path component is forbidden: {component!r}")
    reserved_stem = folded.split(".", 1)[0]
    if reserved_stem in WINDOWS_RESERVED:
        raise ValueError(f"reserved Windows path component is forbidden: {component!r}")
    has_glob = any(character in component for character in GLOB_CHARACTERS)
    if has_glob and not allow_globs:
        raise ValueError(f"wildcards are not allowed here: {component!r}")
    if "**" in component:
        raise ValueError(f"recursive wildcards are forbidden: {component!r}")


def normalize_repo_path(value: str, *, allow_globs: bool) -> PurePosixPath:
    """Return a portable relative path after rejecting aliases and broad roots."""
    if not isinstance(value, str):
        raise ValueError("path must be a string")
    parts = _raw_parts(value)
    for component in parts:
        _validate_component(component, allow_globs=allow_globs)
    if any(character in parts[0] for character in GLOB_CHARACTERS):
        raise ValueError(f"the first path component must be a literal bounded root: {value!r}")
    return PurePosixPath(*parts)


def canonical_scope_root(value: str) -> tuple[str, ...]:
    """Return a case-folded literal ownership root for a validated write scope."""
    path = normalize_repo_path(value, allow_globs=True)
    root: list[str] = []
    for component in path.parts:
        if any(character in component for character in GLOB_CHARACTERS):
            break
        root.append(component.casefold())
    if not root:
        raise ValueError(f"write scope has no bounded literal root: {value!r}")
    return tuple(root)


def scopes_overlap(first: Iterable[str], second: Iterable[str]) -> bool:
    """Conservatively compare write scopes using portable case-insensitive semantics."""
    for left in first:
        left_root = canonical_scope_root(left)
        for right in second:
            right_root = canonical_scope_root(right)
            if left_root[: len(right_root)] == right_root or right_root[: len(left_root)] == left_root:
                return True
    return False


def contains_excluded_component(path: PurePosixPath) -> bool:
    return any(
        component.casefold() in EXCLUDED_COMPONENTS or component.casefold().endswith(".pyc")
        for component in path.parts
    )


def resolved_scope_identity(repository_root: Path, value: str) -> str:
    """Resolve existing aliases in a write scope and return a portable ownership identity."""
    repository_root = repository_root.resolve(strict=True)
    if not repository_root.is_dir():
        raise ValueError("repository root must be a directory")
    scope = normalize_repo_path(value, allow_globs=True)
    current = repository_root
    for component in scope.parts:
        if any(character in component for character in GLOB_CHARACTERS):
            break
        candidate = current / component
        if candidate.exists() or candidate.is_symlink():
            current = candidate.resolve(strict=False)
        else:
            current = candidate
    try:
        relative = PurePosixPath(current.relative_to(repository_root).as_posix())
    except ValueError as exc:
        raise ValueError(f"write scope resolves outside the repository: {value!r}") from exc
    if not relative.parts or relative.as_posix() == ".":
        raise ValueError(f"write scope resolves to the repository root: {value!r}")
    if contains_excluded_component(relative):
        raise ValueError(f"write scope resolves into excluded metadata or cache content: {value!r}")
    return "/".join(component.casefold() for component in relative.parts)
