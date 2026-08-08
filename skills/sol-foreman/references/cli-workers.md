# Codex and Claude CLI workers

Use external CLI processes for exact seat control, cross-family independence, or when native collaboration is unavailable. A CLI worker is not a native subagent; manage it as a subprocess.

## Contents

- [Safe probe](#safe-probe)
- [Consent](#consent)
- [Durable tickets](#durable-tickets)
- [Portable launcher](#portable-launcher)
- [Harness-visible Claude CLI transport](#harness-visible-claude-cli-transport)
- [Model-pinned Codex](#model-pinned-codex)
- [Claude CLI](#claude-cli)
- [Process management](#process-management)
- [Collect and grade](#collect-and-grade)
- [Fable permission prompt](#fable-permission-prompt)

## Safe probe

Before any model call, resolve `<skill-root>` from the loaded `SKILL.md` and
run the bundled sanitized probe:

    python3 "<skill-root>/scripts/probe_capabilities.py" --json

Use only the probe's sanitized capability and authentication-presence fields
in tickets, logs, and reports. Do not invoke `claude auth status` directly
outside the sanitizer, and never print, redirect, or persist its raw response
or any other raw Claude authentication response. Do not print credential files,
environment variables, tokens, or provider configuration. Authentication
presence does not establish model entitlement.

The probe inspects versions and the local Codex model cache without making
billable model calls. Use `py` in place of `python3` on Windows.

## Consent

An explicit request to use Sol Foreman, Codex agents, or Claude agents consents to ordinary dispatches for that task. Announce the planned provider, seat, effort, number of workers, and write authority before the first fan-out.

When the skill triggered implicitly, obtain confirmation before the first external CLI model call.

Always obtain separate permission for Fable 5 unless the user already requested it in the current session. Do not route to Mythos as a workaround for policy refusal.

## Durable tickets

Write each ticket to a file under `.foreman/scratch/` when repository writes are authorized, or to a secure temporary directory for read-only tasks. Pipe the file over stdin to avoid shell quoting corruption.

Do not place secrets in tickets. Give file paths, not copied environment values.
Do not repeat the Sol Foreman invocation or ask an execution worker to load the
orchestration skill; pass the already-derived task contract directly. Mark the
role as bounded execution and explicitly forbid loading orchestration skills,
delegating, and reading outside the supplied repository/context paths.

Before dispatch, create and verify every ticket, raw-stream, and final-report
parent directory. A successful model turn followed by a missing output artifact
is an evidence failure; preserve the parent execution trace and repair the
collection path before accepting the task.

## Portable launcher

Use `scripts/run_cli_worker.py` for the required execution path. It passes the ticket over stdin without a shell, preserves stdout and stderr byte-for-byte, records process identity/timing/exit status in an atomic JSON receipt, and works through `python3` or the Windows `py` launcher.

Provide the worker command as arguments after `--`:

    python3 "<skill-root>/scripts/run_cli_worker.py" \
      --cwd <absolute-work-directory> \
      --ticket <ticket-path> \
      --stdout <raw-stream-path> \
      --stderr <stderr-path> \
      --receipt <receipt-path> \
      -- <worker> <worker-arguments>

The line breaks are illustrative. Pass the same argument vector through the active process tool or on one line on any platform; do not copy shell continuation syntax into an incompatible shell. Use fresh evidence paths for every attempt; the launcher refuses overwrites. For blind verification, set `--cwd <candidate>`, add `--protected-root <source>` and `--protected-root <candidate>`, and add `--read-only-cwd-root <candidate>`. This permits the candidate as the explicitly read-only working tree while rejecting the protected source as `cwd`; all evidence still belongs outside both trees.

Never place secrets in command arguments. The receipt intentionally records the argument vector. For conservative privacy, its command and launcher-error metadata redact every `http(s)` URL, not merely gateway endpoints; that sanitizer never changes the worker's raw stdout or stderr artifacts. The receipt is written with `status: running` immediately after spawn through an atomic create that refuses an existing receipt, then atomically replaced with `status: terminal`, timing, exit data, cancellation status, and process-tree closure. On POSIX, the wrapper combines process-group closure with an inherited per-run token so it can find descendants that detach into another session; if the token scan is unavailable, closure is reported false. On Windows, the worker starts suspended, is assigned to a kill-on-close Job Object, and is then resumed, closing the pre-assignment spawn window; cancellation retains a task-tree fallback. Poll the raw stream, receipt, and wrapper process for long runs; do not accept a receipt whose `process_tree_closed` is not true.

## Harness-visible Claude CLI transport

When the active Codex collaboration surface renders native subagents as live
activity, dispatch a long Claude CLI worker through one thin native-Codex
transport wrapper. The wrapper appears as the visible work item and returns a
completion notification to the lead. The Claude process itself remains a
subprocess behind that wrapper; it is **not** a native Codex agent and is not
independently visible in the harness. The direct `run_cli_worker.py` path only
exposes raw stream files and a receipt, so use it directly when native-agent
visibility is unavailable or the call is short enough that wrapper overhead is
not worthwhile.

The wrapper is transport, not a second execution worker. Its ticket must name
the absolute paths and exact argument vector for one `run_cli_worker.py`
invocation. It must:

1. Run that exact launcher invocation once, with the supplied timeout; never
   compose a raw `claude` command, add shell operators, or retry it.
2. Make no repository edits, analysis, acceptance decision, or subagent
   dispatch. It may write only the ticket, raw stdout/stderr, and receipt files
   already named by the lead.
3. Relay the transport envelope (launcher exit code and the receipt's `pid`,
   `status`, `process_tree_closed`, and artifact paths) separately from the
   Claude worker's final raw message. The worker's own first-line status or
   verdict remains authoritative; the transport envelope is not a worker
   report.

This is the narrow exception to the skill's no-fan-out rule: transcript review
can prove one wrapper and one fixed launcher invocation, but a general shell
cannot mechanically prevent a wrapper from breaking contract. Treat a raw
`claude` call, a second launcher call, or any wrapper edit as a scope breach
that voids the dispatch.

| Observation | Treatment |
|---|---|
| Launcher exits nonzero or receipt is missing | Underlying worker is `BLOCKED`; preserve stderr and receipt evidence. |
| Receipt says `process_tree_closed: false` | `BLOCKED`; do not reconcile or retry until process closure is independently proved. |
| Launcher exits 0 but no parseable worker status/verdict is relayed | `NEEDS FIX` for malformed collection; retain raw artifacts. |
| Wrapper is silent past its deadline | Wrapper is `LOST`; inspect its receipt and token/process evidence, terminate any live child, reconcile the workspace, then decide whether a new attempt is allowed. |
| Served-model metadata is absent or disagrees with the request | Preserve the raw evidence and apply the provenance-label rules in `models-and-routing.md`; wrapper visibility does not confirm a seat. |

## Model-pinned Codex

Read-only analysis or verification worker arguments:

    codex exec --json --output-last-message <report-path> -m <verified-model> -c model_reasoning_effort=<level> --sandbox read-only --ephemeral -C <absolute-repo-path> -

Implementation worker arguments:

    codex exec --json --output-last-message <report-path> -m <verified-model> -c model_reasoning_effort=<level> --sandbox workspace-write --ephemeral -C <absolute-repo-path> -

The portable launcher provides the ticket stdin and captures the JSONL stream; do not add shell redirection or a pipeline. Preserve the JSONL stream as well as the report and do not make the summary the only durable evidence. Do not use
`--dangerously-bypass-approvals-and-sandbox` unless the user explicitly
authorizes it and an external isolation boundary makes it safe.

A read-only sandbox may block network access or commands that write caches. Distinguish sandbox limitations from product defects and record unrun checks.

## Claude CLI

Run `claude --help` immediately before composing a Claude command and record
the version with the verification evidence. Do not use the following general
read-only command for blind verification; use the hardened template in
[`verification.md`](verification.md#hardened-claude-blind-verifier) instead.

Fresh non-blind read-only worker arguments:

    claude -p --model <verified-model-or-alias> --effort <level> --no-session-persistence --output-format stream-json --verbose --permission-mode dontAsk --allowed-tools Read,Grep,Glob,Bash --add-dir <absolute-context-path>

Implementation worker arguments in a trusted, authorized repository:

    claude -p --model <verified-model-or-alias> --effort <level> --no-session-persistence --output-format stream-json --verbose --permission-mode acceptEdits --allowed-tools Read,Grep,Glob,Edit,Write,Bash --add-dir <absolute-context-path>

The portable launcher supplies the prompt over stdin and captures the raw stream and receipt outside the worker tree.

Use `--fallback-model` only for availability failures and only when every fallback clears the task's quality bar. Never use fallback to route around a policy refusal.

Use `--max-budget-usd` when API-key billing is active and a bounded amount is appropriate. It applies to print-mode API calls, not every subscription flow.

`--no-session-persistence` is required for blind verification. Use a persistent session only for a deliberate iterative implementation loop, and record its ID.

Removing Edit and Write tools does not make Bash read-only. Combine tool restrictions with a narrow working directory, explicit bans, before/after repository status, no production credentials, and preferably a read-only copy or worktree for sensitive verification.

When a required Claude flag is absent, use `claude --help` to discover and
record a supported equivalent before dispatch. Never silently drop a required
isolation control. If the installed CLI has no equivalent for a required
control, stop the blind-verification run as `NEEDS_CONTEXT` and use a
separately authorized verification method.

## Process management

For a long task:

1. Start it through the available execution tool without blocking user communication indefinitely.
2. Record process/session identity, provider, model, effort, ticket path, output path, and start time.
3. Poll for output and process state.
4. Preserve structured output or the final report.
5. Check the exit code.
6. Confirm the worker stopped before reconciling or retrying.
7. Inspect repository status and artifacts.

Treat a missing required report, truncated raw stream, or failed output-path
write as `NEEDS FIX` even when the model process itself exited successfully.

Do not use a fixed short timeout to classify a capable agent as absent. Do not abandon a background process.

## Collect and grade

Check:

- process exit status;
- exact model/effort confirmation when available;
- required status or verdict first line;
- files actually changed;
- commands actually executed;
- evidence mapped to each criterion;
- repository cleanliness and scope;
- unsupported claims or unverified items.

Parse JSON defensively. A successful process exit can still contain a `BLOCKED` report or failed acceptance criteria.

## Fable permission prompt

Keep the request concrete:

    I recommend Claude Fable 5 for <specific lane> because <material capability
    advantage over Sol/Opus/Sonnet>. It uses a distinct, expensive Claude quota.
    May I dispatch one Fable 5 worker at <effort> with <read/write scope>?

If permission is denied, reroute only if another seat still clears the quality bar.
