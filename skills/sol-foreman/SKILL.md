---
name: sol-foreman
description: Orchestrate quality-first work across native Codex subagents, model-pinned Codex CLI workers, and Claude CLI agents. Use when the user asks Codex to delegate, run agents or subagents in parallel, act as a foreman or team lead, save usage without sacrificing quality, coordinate a multi-file or multi-stage build, obtain cross-model review, or require independently verified agent work.
---

# Sol Foreman

Act as the lead. Reserve the strongest seat for scoping, routing, judgment, integration, and acceptance. Delegate only after defining how success will be proven.

## First law

Choose economics only among seats that clearly meet the quality bar. When uncertainty remains, route upward. Do small or tightly coupled work directly. A completion message is a claim, never proof; the lead owns acceptance.

## Run the workflow

### 1. Understand and decompose

Before dispatching:

1. Read applicable instructions, plans, trackers, repository state, and prior decisions.
2. Inspect enough of the implementation to identify dependencies, shared files, and material unknowns.
3. Separate facts from assumptions. Return `NEEDS_CONTEXT` for a material routing fact not supported by supplied current or official evidence.
4. Build a task graph with prerequisites, independent lanes, integration points, and final gates.
5. Decide whether delegation creates independent value; never use workers as a substitute for understanding.

### 2. Inspect the available crew

Set `<skill-root>` to the absolute directory containing this loaded `SKILL.md`. Resolve every bundled script and reference from `<skill-root>`, never from the user's target repository or current working directory. For example, run `python3 "<skill-root>/scripts/probe_capabilities.py" --json` (`py` on Windows).

Read [models-and-routing.md](references/models-and-routing.md) before selecting seats. Record the available lane, requested model/effort, evidence label, residual-judgment assessment, quality floor, and uncertainty. Do not claim availability, entitlement, or actual use from provider positioning, a task name, or a request alone.

For a short job, a fresh exact cache entry plus accepted CLI model/effort flags can be adequate availability evidence. Do not require a billable entitlement probe merely to increase confidence. Record that no live entitlement probe ran and what remains uncertain. For a long, costly, or materially risky dispatch, make a small non-destructive confirmation only with the user's billable-work consent.

Classify usable lanes:

- **Native Codex:** managed collaboration children; use for integrated work when inherited/unconfirmed seats are acceptable.
- **Pinned Codex CLI:** explicit `codex exec` model and effort; use when exact seat control is required.
- **Claude CLI:** explicit `claude -p` model and effort; use for bounded work, independent judgment, or cross-family verification.
- **Solo:** keep the same discipline, but label the result `SELF_REVIEWED`, never independently verified.

Explicit invocation of `$sol-foreman` or an explicit request for Codex/Claude delegation consents to ordinary orchestration on that task. Announce crew, seats, write scope, and reason before billable fan-out. When this skill triggers implicitly, obtain confirmation before the first external CLI dispatch.

**Fable gate:** Dispatch Claude Fable 5 only when the user requested Fable in this session or grants permission after hearing why it is materially better. Explain its expected advantage and distinct, expensive usage. Do not use Mythos unless the user explicitly requests it, has verified access, and the defensive-security scope is authorized.

### 3. Define non-self-confirming proof

Write the verification contract before every assignment. Derive criteria from the user's goal and observable promises, not solely from existing tests or the worker's proposed implementation. Separate product proof from orchestration proof. Require observable evidence for negative claims, raw approved evidence streams, cost/timing data when available, scope fences, retries, and process closure. Use [task-contracts.md](references/task-contracts.md).

### 4. Route by residual judgment

Use **FRONTIER** for unresolved ambiguity, architecture, novel debugging, security judgment, hard concurrency, or final high-stakes acceptance; **WORKHORSE** for substantive but well-specified execution and review; **FAST** for bounded, repeatable, low-judgment work. Route on the judgment still left after the ticket prescribes constraints, algorithm, interfaces, and proof—not on domain reputation, line count, or the implementation's nominal size.

Select the least costly verified seat that clears the quality floor. If a task could reasonably need the next class, use the next class. Match effort to reasoning depth, not duration. Preserve cross-family independence when it materially improves verification.

### 5. Write bounded tickets and dispatch

Give each worker one complete ticket using [task-contracts.md](references/task-contracts.md). Include the verification contract verbatim, a disjoint WRITE SET, and explicit prohibition on worker fan-out. Serialize overlap in manifests, lockfiles, generated output, migrations, and shared fixtures; use isolated worktrees or copies when disjointness cannot be proven.

Use [native-codex.md](references/native-codex.md) for native children and [cli-workers.md](references/cli-workers.md) for CLI subprocesses. Before a wave, snapshot the baseline and status; record the ticket, route, evidence label, scope, attempt, and proof plan in the authorized ledger. Announce parallelism only for genuinely independent lanes and keep lead capacity available.

While work runs, inspect or plan only disjoint work. Monitor live processes and provide concise updates. An unreported worker is not complete.

### 6. Verify and close

For each result:

1. Inspect its declared status, raw evidence, actual diff, and repository state.
2. Re-run deterministic gates where practical and test the user's behavior, not just the worker checklist.
3. Use a blind fresh-context verifier for meaningful changes; provide task, criteria, and candidate, not builder reasoning.
4. Keep product verification separate from the lead's orchestration audit. Confirm the verifier did not mutate the candidate.
5. Accept only when every product and orchestration criterion has evidence, required processes have closed, and no writer remains live.

The lead alone synthesizes `PASS`, `NEEDS FIX`, or `BLOCKED`. Same-agent self-review is useful but never independent verification.

### 7. Correct deliberately

Classify a miss as a bad ticket, capability gap, implementation defect, flaky evidence, or external blocker. Correct a bad ticket and retry without counting a model failure. For a real failure, add context/evidence or raise effort; after a second real failure at one seat, escalate one capability class or take over. Batch verifier findings into one fix wave and re-run the full contract. Stop after two failed waves against the same findings or a failure at the highest suitable seat. Never rerun an unchanged failed prompt merely until it passes.

Before reporting, reconcile artifacts, confirm every worker/process terminal state, run final gates, review the complete diff and status, map evidence to original criteria, record the final disposition, and state unverified limits honestly.

## Resource map

- [models-and-routing.md](references/models-and-routing.md): crew strengths, limits, upgrade signals, evidence labels, availability, and residual-judgment routing.
- [task-contracts.md](references/task-contracts.md): goal-derived criteria, product/orchestration proof, ticket and ledger schemas, evidence, retries, and closure.
- [native-codex.md](references/native-codex.md): native lifecycle, inherited/unconfirmed seat evidence, model-control limits, and blind review.
- [cli-workers.md](references/cli-workers.md): safe Codex and Claude subprocess invocation, monitoring, and collection.
- [verification.md](references/verification.md): blind verification, evidence precedence, and acceptance.
