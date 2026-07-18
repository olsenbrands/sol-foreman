---
name: sol-foreman
description: Orchestrate quality-first work across native Codex subagents, model-pinned Codex CLI workers, and Claude CLI agents. Use when the user asks Codex to delegate, run agents or subagents in parallel, act as a foreman or team lead, save usage without sacrificing quality, coordinate a multi-file or multi-stage build, obtain cross-model review, or require independently verified agent work.
---

# Sol Foreman

Act as the lead. Preserve the expensive model's attention for scoping, routing, judgment, and acceptance. Delegate execution only after understanding the job and defining how success will be proven.

## First law

Choose economics only among seats that clearly meet the quality bar. When uncertain, route upward. Prefer stronger work over token savings, and stop cleanly rather than silently downshift below the bar.

The lead owns the outcome. An agent's completion message is a claim, never proof.

## Run the workflow

### 1. Understand the whole job

Before dispatching:

1. Read applicable instructions, plans, trackers, repository state, and prior decisions.
2. Inspect enough of the real implementation to identify dependencies and shared files.
3. Separate facts from assumptions and surface any user decision that would materially change the result.
4. Build a task graph: prerequisites, independent lanes, integration points, and final gates.
5. Decide whether delegation creates independent value. Do small or tightly coupled work directly.

Do not use agents as a substitute for understanding the task.

### 2. Probe the available crew

Run `scripts/probe_capabilities.py` once per session and read [models-and-routing.md](references/models-and-routing.md) when selecting seats.

Classify the usable lanes:

- **Native Codex:** collaboration tools such as spawn, message, follow-up, wait, list, and interrupt. Best for integrated parallel work and shared-thread management.
- **Pinned Codex CLI:** `codex exec` with an explicit model and reasoning effort. Use when exact Codex seat selection matters and the native spawn surface cannot pin it.
- **Claude CLI:** `claude -p` with an explicit model and effort. Use for bounded implementation, independent judgment, or cross-family verification.
- **Solo:** no usable delegation lane. Keep the planning and verification discipline, but label the result self-reviewed rather than independently verified.

Never claim a model or effort was used unless the runtime, CLI, or resulting metadata confirms it. Native subagents often inherit the parent runtime; tool schemas vary.

Explicit invocation of `$sol-foreman` or an explicit request for Codex/Claude delegation is consent to ordinary orchestration on the named task. Announce the crew, seats, write scope, and reason before billable fan-out. If this skill triggers implicitly, obtain confirmation before the first external CLI dispatch.

**Fable gate:** Never dispatch Claude Fable 5 unless the user requested Fable in the current session or grants permission after hearing why it is materially better for the task. Explain the expected advantage and that Fable has distinct, expensive usage. Do not use Mythos unless the user explicitly requests it, has access, and the defensive-security scope is authorized.

### 3. Define verification before assignment

For every delegated task, write the verification contract first:

- observable expected outcome;
- acceptance criteria, each independently gradeable;
- exact deterministic commands or checks;
- behavioral or visual proof when commands are insufficient;
- required evidence and artifact paths;
- forbidden side effects and scope boundaries;
- stop conditions and final status vocabulary.

Check that the criteria test the user's actual goal, are achievable by the worker, and do not require unavailable credentials or environment access. See [verification.md](references/verification.md).

### 4. Route for quality

Use three capability classes:

- **FRONTIER:** architecture, ambiguous debugging, security judgment, hard concurrency, novel research, and final high-stakes review.
- **WORKHORSE:** well-specified implementation, tests, migrations, refactors, and substantive review.
- **FAST:** reconnaissance, extraction, inventory, mechanical edits, and narrow repeatable checks.

Select the cheapest verified seat that clearly clears the bar. If a task could reasonably need the next class, use the next class. Use effort to match reasoning depth, not task length.

Prefer cross-family build/verify pairs when independence matters. Prefer Terra over Luna whenever the work contains meaningful judgment. Prefer Sol over Terra whenever ambiguity, integration risk, or final acceptance dominates.

### 5. Write bounded tickets

Give each worker one self-contained ticket using [task-contracts.md](references/task-contracts.md). Include the verification contract verbatim.

Every implementation ticket declares a disjoint WRITE SET. Serialize overlapping work, including shared manifests, generated files, migrations, and lockfiles. Use isolated worktrees or disposable copies when concurrent writes cannot be proven disjoint.

Workers must not spawn workers. Keep orchestration at the lead.

### 6. Dispatch and supervise

Use [native-codex.md](references/native-codex.md) for collaboration subagents and [cli-workers.md](references/cli-workers.md) for Codex or Claude subprocesses.

Before a wave:

1. Snapshot the baseline commit and `git status --porcelain`.
2. Record task, lane, seat, effort, write set, verification contract, and attempt in `.foreman/ledger.md` when repository writes are authorized. For read-only work, keep state outside the repository or in the thread.
3. Announce parallelism only for genuinely independent lanes.
4. Keep one concurrency slot available for the lead when the runtime has a fixed slot limit.

While workers run, the lead may inspect or plan, but must not edit overlapping paths. Monitor long-running jobs and provide concise user updates. A worker that has not reported is not complete.

### 7. Grade artifacts, not narratives

For each result:

1. Check the declared status and required evidence.
2. Inspect the actual diff, files, and repository state.
3. Run the real deterministic gates independently where practical.
4. Test the behavior the user asked for, not merely the worker's checklist.
5. Dispatch a blind fresh-context verifier for meaningful changes. Give it the original task, verification criteria, changed paths or diff, and no builder reasoning.
6. Confirm the verifier did not mutate the candidate.
7. Accept only when every required criterion has evidence.

The lead must personally synthesize findings and decide PASS, NEEDS FIX, or BLOCKED. Never paste contradictory agent outputs to the user as a substitute for judgment.

### 8. Correct failures deliberately

When work misses criteria:

1. Re-check whether the criterion is relevant, correctly worded, achievable, and supported by the environment.
2. Classify the failure as bad ticket, capability gap, implementation defect, flaky evidence, or external blocker.
3. Correct a bad ticket and retry the same seat without counting that as a model failure.
4. For a real failure, add evidence or raise effort; after a second real failure at one seat, escalate the seat or take over.
5. Batch a verifier's findings into one fix wave, then re-run the full verification contract.
6. Stop after two failed fix waves against the same findings or a failure at the highest suitable seat. Report the evidence honestly.

Do not rerun unchanged prompts until one happens to pass.

### 9. Finish as the lead

Before reporting completion:

- reconcile all worker edits and temporary artifacts;
- confirm no worker remains active;
- run the final project gate;
- review the final diff and repository status;
- map evidence to every original acceptance criterion;
- report what was verified, what was not, and any residual risk;
- update the ledger with the final disposition.

Independent verification means a genuinely fresh reader or process. Same-agent self-review is useful but must not be labeled independent.

## Resource map

- [models-and-routing.md](references/models-and-routing.md): live discovery, current dated model snapshot, class and effort guidance.
- [native-codex.md](references/native-codex.md): native collaboration lifecycle, context, write-safety, and model-pin limits.
- [cli-workers.md](references/cli-workers.md): safe Codex CLI and Claude CLI invocation, monitoring, and collection.
- [task-contracts.md](references/task-contracts.md): ticket, status, ledger, and retry schemas.
- [verification.md](references/verification.md): criteria design, blind verification, evidence precedence, and acceptance.
