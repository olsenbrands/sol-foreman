# Conditional execution tools

Native managed agents are the default when suitable. These bundled Python 3
standard-library tools are used for concrete execution risks, not as a reason to
initialize a program framework. Resolve paths relative to this skill and inspect
each tool's help before first use. Do not require unrelated helpers for native work.

- `probe_capabilities.py --json`: sanitized Codex/Claude capability and auth
  discovery. Its bundled model snapshot is older than this policy; use current
  runtime evidence. It does not probe Grok. Discover Grok separately without
  exposing credentials. Cache discovery within the run and refresh on a reason.
- `run_cli_worker.py`: mandatory wrapper for optional CLI model execution when
  usable on the current platform. Pass an argument vector after `--`, prompt file
  via `--ticket`, explicit `--cwd`, and new stdout/stderr/receipt paths. It feeds
  stdin without a shell, preserves raw streams, and records lifecycle evidence.
  Retain the wrapper's process handle; use a finite task-specific checkpoint and
  interrupt/collect it if the run must stop. A terminal receipt is not acceptance.
  Require `process_tree_closed: true` or independently establish closure before
  releasing writer ownership. Missing lifecycle capability means use native
  execution or lead work, not silently weaken closure. Raw streams remain private.
- `materialize_candidate.py` plus `path_policy.py`: create a product-only review
  copy from an explicit relative-path allowlist. It rejects unsafe paths and
  excluded metadata, and dereferences safe internal symlinks. If link identity is
  part of correctness, use a suitable alternate isolation method instead.
- `fingerprint_tree.py --manifest`: compare complete source and candidate product
  contents before/after a tool-enabled review. Keep reviewer output outside both
  trees. Mutations invalidate affected review evidence; reconcile before repair.

For a CLI reviewer, use a fresh isolated candidate; disable ambient skills,
hooks/customizations, MCP and browser access as supported, and restrict tools to
read-only operations. An allowlist including a shell is not a sandbox. Preserve
before/after fingerprints and raw evidence. The reviewer does not fix the files.
Use `--protected-root` for original and candidate roots and designate only the
candidate through `--read-only-cwd-root` when invoking the wrapper for review.

This bundle does not include or require the legacy JSON preflight/program guard
for new runs. Its review guard bounds review reservations only; it does not
enforce execution write sets, prevent every duplicate launch, or replace project
guards. Enforce ownership through the runtime, isolation, and lead reconciliation
as described by the main workflow. Do not claim removed mechanical guarantees.

Existing hard user restrictions remain binding. Fable or other separately
restricted premium pools are not implicitly authorized by a generic provider
preference. Permission refusals must never be treated as quota failures.
