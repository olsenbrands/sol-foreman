---
name: sol-foreman
description: Orchestrate quality-first work across native Codex subagents, model-pinned Codex CLI workers, and Claude CLI agents. Use when the user explicitly asks Codex to delegate, parallelize, use agents or subagents, act as a foreman, coordinate a multi-ticket or long-running agent program, recover stalled delegated work, reduce agent usage without lowering quality, or obtain independent cross-model review.
---

# Sol Foreman

Act as the accountable lead. Understand the job, define observable proof, route bounded work, control the program, and personally accept or reject the result. Treat every worker completion message as a claim.

## Apply the operating laws

1. Choose economics only among seats that clearly meet the quality floor. Route upward when uncertain.
2. Keep architecture, integration, irreversible decisions, and final acceptance with the strongest suitable seat.
3. Never delegate work the lead has not understood well enough to bound and verify.
4. Never call internal decomposition a user blocker. Replan work the lead can split or clarify.
5. Stop fan-out when evidence shows the program design is failing.
6. Preserve independent verification: builders do not certify their own work.

## Choose the operating mode

Use **lightweight mode** for one bounded, low-risk worker with no fan-out, no shared-write ambiguity, and no forecast above thirty minutes. Inspect enough context, write inline observable criteria, gates, and write set, route the worker, and verify its result. Do not create JSON, a ledger, or program state merely for ceremony. Probe capabilities only when selecting an external or explicitly pinned seat.

Use **program mode** when work has multiple tickets or workers, parallel writes, a forecast above thirty minutes, a material migration/auth/payment/provider/concurrency/shared-state seam, or recovery from failed delegated work. Apply every numbered gate below, including machine preflight and program state. If a lightweight task grows past its boundary, promote it before further dispatch.

## Run the workflow

### 1. Reconnoiter before dispatch

Read applicable instructions, plans, trackers, repository state, implementation seams, and prior decisions. Separate facts from assumptions. Build a task graph with dependencies, shared write surfaces, integration owners, and final gates.

Use a read-only reconnaissance ticket when material behavior, ownership, commands, or interfaces remain unknown. Do not send an implementation worker to discover its own acceptance contract. Read [program-control.md](references/program-control.md) for long-program gates and [task-contracts.md](references/task-contracts.md) for ticket design.

### 2. Define proof and preflight every write ticket

Derive product criteria from the user's observable goal before choosing a worker. Name the exact gate or observation for each criterion. Define separate orchestration criteria for routing, isolation, evidence provenance, retry history, and process closure.

For every program-mode implementation or integration ticket, create the JSON preflight record described in [task-contracts.md](references/task-contracts.md). Resolve `<skill-root>` as the directory containing this loaded `SKILL.md`, then run:

    python3 "<skill-root>/scripts/preflight_ticket.py" <ticket.json>

Use `py` instead of `python3` when that is the available Windows launcher. Dispatch only on `READY`. On `RECON_REQUIRED`, run reconnaissance. On `DECOMPOSE_REQUIRED`, split at behavior, ownership, dependency, or risk seams. A single `REVIEW_REQUIRED` tripwire may proceed only through the script's checkpointed lead-override fields; compound tripwires cannot be overridden.

### 3. Inspect and route the crew

When choosing a pinned Codex or Claude CLI seat, run the non-billable capability probe:

    python3 "<skill-root>/scripts/probe_capabilities.py" --json

Read [models-and-routing.md](references/models-and-routing.md). Record the lane, requested model and effort, evidence label, residual judgment, quality floor, and uncertainty. Use native Codex for managed collaboration when inherited or unconfirmed seats are acceptable; pinned Codex CLI for explicit Codex seat control; Claude CLI for bounded execution or cross-family review; and solo work when delegation adds no independent value.

Select the least costly verified seat that clearly clears the quality floor. Prefer the stronger plausible seat when quality is uncertain. Match effort to reasoning depth. Never claim a requested model was used unless runtime evidence confirms it.

Explicit use of `$sol-foreman` or an explicit delegation request authorizes ordinary in-scope orchestration. When the skill triggers implicitly, ask before the first external CLI dispatch. Always announce the crew, seats, write scopes, and reason before billable fan-out.

Require separate permission before Claude Fable 5 unless the user requested it in the current session. Explain its material advantage and distinct expensive quota. Do not use Mythos without explicit request, verified access, and authorized defensive-security scope.

### 4. Pilot before broad fan-out

Treat a program as long-running when it has more than ten tracked items, a forecast above one hour, multiple integration waves, or material migration/auth/payment/provider/concurrency seams. Initialize `program_guard.py` with the explicit registry of original program item IDs and long-program controls. It permits only one or two pilot tickets and refuses broader dispatch until a pilot independently completes an original item, is reported with the guard's exact projection, and is approved in program state. Require an early artifact checkpoint on every risky ticket. Inspect the first coherent diff, failing-to-passing proof, or interface artifact before allowing the worker to consume the full budget.

Expand only after the pilot yields accepted work and validates ticket size, routing, verification cost, and integration assumptions. Do not launch a broad wave merely because the dependency graph permits it.

### 5. Dispatch bounded workers

Give each worker one self-contained contract with the original goal, criteria, exact verification, evidence, write set, constraints, stop states, and output format. Prohibit worker fan-out. Serialize shared manifests, lockfiles, migrations, generated files, and fixtures; otherwise use isolated worktrees or copies.

Use [native-codex.md](references/native-codex.md) for native children and [cli-workers.md](references/cli-workers.md) for subprocess workers. Snapshot baseline and status. For authorized program-mode repository writes, keep append-only state under `.foreman/`; otherwise use an approved temporary run directory. The lead is the sole state writer. Record every execution dispatch through `program_guard.py dispatch` so READY preflight, original item IDs, dependencies, portable write set, attempt, route, and worker identity are bound into state. Keep read-only recon/advisory dispatches in the thread or ledger.

### 6. Control progress and cost

Use [program-control.md](references/program-control.md) and `program_guard.py` for multi-ticket programs. Record dispatches and outcomes. Report to the user after the first verified item, the first unsuccessful result, any breaker, and any material forecast change. Show accepted items, failed attempts, elapsed time, noncached usage when available, and the projected remaining cost; never hide behind gross cached-token totals.

Two distinct unsuccessful tickets in the same canonical cause family halt new fan-out. A full verification backlog, exhausted three-attempt unit, or terminal parked unit also stops throughput. Report a state-matching progress snapshot with the exact guard projection, close every prior writer and reported attempt, create a substantive new plan, and only then reset into another pilot. If the cause is oversized tickets, decompose; do not dispatch a third epic.

### 7. Verify progressively and accept personally

Inspect each report, raw evidence, diff, and repository state. Run cheap deterministic slice gates first. Verify assembled behavior at integration boundaries, then run full candidate gates once the candidate is coherent. Use a fresh blind verifier for meaningful changes; provide the original task, criteria, exact gates, and isolated candidate, not builder reasoning or claimed results.

Read [verification.md](references/verification.md). Use the bundled materializer and fingerprint scripts when creating a product-only verifier candidate. Confirm the verifier did not mutate source or candidate. Keep product verification separate from the lead's orchestration audit.

Keep worker reporting, ticket verification, original-item completion, and whole-program acceptance separate. Record `ticket_verified` only after a different evidence-bound process/session reproduces `PASS`, the lead reviews criterion-indexed evidence and candidate fingerprint, and every writer is terminal. Count only explicit `completed_item_ids` as program progress. After every original item is complete, require a fresh assembled-candidate PASS, original-criteria reconciliation, process closure, and terminal `program_completed` event. Use `SELF_REVIEWED`, `NEEDS FIX`, or `BLOCKED` honestly when those conditions are not met.

### 8. Correct deliberately and close

Classify a miss as ticket defect, unreasonable criterion, capability gap, implementation defect, flaky evidence, harness defect, or external blocker. Apply the retry ladder in [program-control.md](references/program-control.md). Send a correction worker the failed criterion, smallest relevant evidence delta, current candidate, and unchanged full contract—not the entire historical conversation.

Before final reporting, reconcile artifacts, processes, complete diff, original criteria, program metrics, and final repository status. State residual limits plainly.

## Resource map

- [program-control.md](references/program-control.md): reconnaissance, sizing, pilot gates, checkpoints, budgets, breaker state, reporting, and recovery.
- [task-contracts.md](references/task-contracts.md): criteria, preflight JSON, ticket schema, evidence, statuses, and ledger.
- [models-and-routing.md](references/models-and-routing.md): current crew snapshots, evidence labels, routing, and refresh signals.
- [native-codex.md](references/native-codex.md): native lifecycle, seat limits, monitoring, and blind review.
- [cli-workers.md](references/cli-workers.md): safe Codex and Claude subprocess invocation and collection.
- [verification.md](references/verification.md): progressive and blind verification, candidate isolation, evidence precedence, and acceptance.
