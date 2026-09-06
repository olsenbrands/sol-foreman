# Bounded execution

## Contract

Use only enough detail to make the assignment self-contained. Include:

```text
OUTCOME / ORIGINAL INTENT: user promise and original outcome ID, if tracked
BASELINE / CONTEXT: repository or artifact identity; required instruction/source paths
CRITERIA: observable behavior, negative constraints, and how each is checked
DECISIONS: fixed architecture/interfaces; routine implementation decisions left to
           the worker; relevant uncertainty and escalation boundary
OWNERSHIP: exact worktree and permitted write paths; shared resources and dependencies
ROUTE: requested model/effort, reason, evidence status, budget/checkpoint
BOUNDARIES: authorized effects through checks, ordinary repair, integration, and
            permitted release operations; no delegation, foreman skills, or unrelated changes
STOP: criterion conflict, missing authority, material scope, architecture,
      interface, or risk change, ordinary repair that cannot meet its criterion
      within the stated envelope, unavailable tool, or exceeded envelope;
      return the evidence and partial state; do not improvise a broader task
RETURN: result, changed paths, criterion evidence, exact checks and exits,
        remaining concerns, process/artifact identity, usage or unavailable
```

Use `REPORTED`, `NEEDS_CONTEXT`, or `BLOCKED` as useful report labels; exact prose
format is not a product acceptance gate. Preserve original criterion IDs through
repairs. A scout may report facts and hypotheses but does not approve architecture.
The worker owns routine execution through the authorized delivery boundary. A review
or lead release gate pauses it for evidence or judgment; it does not make the lead
the default repairer. Return a substantiated routine repair to the same builder
first. A takeover needs a recorded concrete cause and bounded stopping point.
Record the dispatch and later its result in the written session crew record
described in [crew-control.md](crew-control.md), including for a small delegated
assignment. This can be one short section of an existing run document.

## Native Codex first when the route fits

Inspect the actual spawn schema. Request the chosen model and supported effort
explicitly when available. For a self-contained worker or blind reviewer use
`fork_turns: "none"` where supported. Full conversation inheritance increases
context cost and contaminates independent review. Record the returned agent ID.

Workers share files unless explicitly placed in an isolated checkout. A native
agent is not a sandbox. Before dispatch, inspect status and compare ownership;
include shared manifests, generated files, lockfiles, fixtures, services, databases,
ports, and credentials, not just source filenames. Reserve integration ownership.

Use completion notifications and relevant artifact checkpoints. Continue useful
disjoint work while waiting; avoid repeated whole-log reads or rapid empty polling.
Reuse an idle builder for a related correction; start a new reviewer context.
Confirm each worker is terminal before integrating over its files or closing.

## Optional CLI routes: Codex, Claude, Grok

Use an installed CLI when native controls cannot request the needed model or an
authorized cross-provider route is useful. CLI dispatch is optional; absence of
one provider does not block work another qualified authorized route can complete.
Never silently substitute a new paid account/provider or an automatic model fallback.
An announced fallback to already-authorized Codex capacity after a Claude/Grok
usage limit is ordinary orchestration, not a new permission gate. Apply
[crew-control.md](crew-control.md); close/reconcile the previous writer first.

Before the first such dispatch, inspect version/help and sanitized auth metadata.
Check supported noninteractive invocation, model/effort controls, output capture,
tool permissions, no-delegation controls, and how to terminate the owned process
tree. Choose a scope-compatible permission mode; do not modify global configuration
or bypass safeguards merely to make a worker run.

Observed invocation surfaces on 2026-09-05, to rediscover before use:

| CLI | Task entry | Model | Effort | Evidence output |
|---|---|---|---|---|
| Codex | `exec`, prompt on stdin | `--model` | config `model_reasoning_effort` | `--json`, `--output-last-message` |
| Claude | `--print`, prompt on stdin | `--model` | `--effort` for supported model | `--output-format stream-json --verbose` |
| Grok | `--prompt-file` | `--model` | `--reasoning-effort` | `--output-format streaming-json` |

Use the bundled tools according to [retained-tools.md](retained-tools.md) for CLI
execution and isolated candidate handling. This table is flag discovery evidence,
not a tested universal launcher. Construct
argument arrays with a process API when possible; prompt text belongs in stdin or
a file, not interpolated shell code. Do not compose shell commands from worker
output. Reuse an existing reviewed launcher if the project provides one; inspect
its permissions, routing, dependencies, and lifetime handling before using it.
The skill does not require Sol/Fable Foreman to be installed.

Create one run directory for prompt, stdout, stderr, receipt, and final report.
Save raw events privately; summarize relevant excerpts without rewriting evidence.
Record command (without secrets), cwd, start/end, exit, process/session identity,
route evidence, and known descendant processes. Retain a handle to interrupt and
collect it. A timeout or a killed parent does not prove descendants are terminal.
If lifecycle control cannot be established, use native management or take over only
with a concrete cause and bounded stopping point.

For Claude review, discover controls such as safe mode, empty strict MCP config,
no persistence, no Chrome, no slash commands, and read-only tools. For Grok,
discover `--no-subagents`, allowed tools, permission mode, and sandbox support.
Restrict tools and filesystem where possible; a prompt saying read-only, or a
tool allowlist that includes shell, is not a security boundary. Review an isolated
candidate and check its content before/after. Keep ambient foreman and archive
instructions out of the candidate when they are not product inputs.

## Failure and repair

Environment failure: reproduce the failing capability outside the worker if safe.
Distinguish worker sandbox/tool limits from a product defect. Move that gate to an
authorized capable environment or lead, preserving independent review of the result.
Do not request broad new permissions if the existing environment already suffices.

On a lost worker, inspect its actual process/thread state, preserve partial edits,
and close it before replacement. Never reset the user's tree or delete unknown
artifacts as routine cleanup. Escalations carry the original contract and smallest
useful failure delta. Record unsuccessful attempts under the original outcome.
