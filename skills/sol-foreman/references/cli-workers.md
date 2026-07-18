# Codex and Claude CLI workers

Use external CLI processes for exact seat control, cross-family independence, or when native collaboration is unavailable. A CLI worker is not a native subagent; manage it as a subprocess.

## Contents

- [Safe probe](#safe-probe)
- [Consent](#consent)
- [Durable tickets](#durable-tickets)
- [Model-pinned Codex](#model-pinned-codex)
- [Claude CLI](#claude-cli)
- [Process management](#process-management)
- [Collect and grade](#collect-and-grade)
- [Fable permission prompt](#fable-permission-prompt)

## Safe probe

Run metadata-only checks before any model call:

    command -v codex
    codex --version
    codex login status

    command -v claude
    claude --version
    claude auth status

Do not print credential files, environment variables, tokens, or provider configuration. Authentication presence does not establish model entitlement.

Run `python3 scripts/probe_capabilities.py` (`py` on Windows) to inspect versions and the local Codex model cache without making billable model calls.

## Consent

An explicit request to use Sol Foreman, Codex agents, or Claude agents consents to ordinary dispatches for that task. Announce the planned provider, seat, effort, number of workers, and write authority before the first fan-out.

When the skill triggered implicitly, obtain confirmation before the first external CLI model call.

Always obtain separate permission for Fable 5 unless the user already requested it in the current session. Do not route to Mythos as a workaround for policy refusal.

## Durable tickets

Write each ticket to a file under `.foreman/scratch/` when repository writes are authorized, or to a secure temporary directory for read-only tasks. Pipe the file over stdin to avoid shell quoting corruption.

Do not place secrets in tickets. Give file paths, not copied environment values.

## Model-pinned Codex

Read-only analysis or verification:

    codex exec \
      -m <verified-model> \
      -c model_reasoning_effort='<level>' \
      --sandbox read-only \
      --ephemeral \
      -C <absolute-repo-path> \
      - < <ticket-path>

Implementation:

    codex exec \
      -m <verified-model> \
      -c model_reasoning_effort='<level>' \
      --sandbox workspace-write \
      --ephemeral \
      -C <absolute-repo-path> \
      - < <ticket-path>

Use `--json` for event-stream monitoring or `--output-last-message <path>` for a clean report artifact. Do not use `--dangerously-bypass-approvals-and-sandbox` unless the user explicitly authorizes it and an external isolation boundary makes it safe.

A read-only sandbox may block network access or commands that write caches. Distinguish sandbox limitations from product defects and record unrun checks.

## Claude CLI

Fresh read-only analysis or verification:

    claude -p \
      --model <verified-model-or-alias> \
      --effort <level> \
      --no-session-persistence \
      --output-format json \
      --permission-mode dontAsk \
      --allowedTools Read,Grep,Glob,Bash \
      --add-dir <absolute-context-path> \
      < <ticket-path>

Implementation in a trusted, authorized repository:

    claude -p \
      --model <verified-model-or-alias> \
      --effort <level> \
      --no-session-persistence \
      --output-format json \
      --permission-mode acceptEdits \
      --allowedTools Read,Grep,Glob,Edit,Write,Bash \
      --add-dir <absolute-context-path> \
      < <ticket-path>

Use `--fallback-model` only for availability failures and only when every fallback clears the task's quality bar. Never use fallback to route around a policy refusal.

Use `--max-budget-usd` when API-key billing is active and a bounded amount is appropriate. It applies to print-mode API calls, not every subscription flow.

`--no-session-persistence` is required for blind verification. Use a persistent session only for a deliberate iterative implementation loop, and record its ID.

Removing Edit and Write tools does not make Bash read-only. Combine tool restrictions with a narrow working directory, explicit bans, before/after repository status, no production credentials, and preferably a read-only copy or worktree for sensitive verification.

## Process management

For a long task:

1. Start it through the available execution tool without blocking user communication indefinitely.
2. Record process/session identity, provider, model, effort, ticket path, output path, and start time.
3. Poll for output and process state.
4. Preserve structured output or the final report.
5. Check the exit code.
6. Confirm the worker stopped before reconciling or retrying.
7. Inspect repository status and artifacts.

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
