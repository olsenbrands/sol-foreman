# Long work, goals, and recovery

## One source of program truth

Reuse the project tracker. Add one run record in a task-local `.foreman/` directory
or authorized temporary location. Keep private runtime artifacts out of published
diffs. This is an instruction-level protocol, not a machine-enforced state guard.
If the project has an existing required guard, operate through it; do not edit its
derived state or discard it to make progress counters convenient.

The lead owns the record. Keep a current checkpoint plus append-only decisions and
attempts. Do not maintain duplicate JSON, Markdown, and chat projections unless
the repository's actual tooling requires them. Record:

```text
Original objective and user-authorized scope; original outcome IDs and criteria
Baseline/revision; repository/worktree; dirty changes and their ownership
Current plan/dependencies; builder and integration owners; final acceptance gates
Routes: requested/observed models and efforts; providers; billing uncertainty
Active workers: IDs, exact workspaces/write sets, attempt, checkpoint, process state
Outcome states: pending / working / review pending / accepted / externally blocked
Evidence: candidate identity, criterion coverage, checks, independent review
Attempts/decisions: root outcome ID, failure cause, change in approach, timestamp
Usage: observed totals by provider, lead when available, unknowns, forecast caveats
Crew record: provider states, current preference, attempt quality and route decisions
Next action; any user decision actually needed; safe recovery instructions
```

Count original accepted outcomes, not supporting tickets. Scope additions are
explicit new outcomes, not silent denominator changes. Preserve accepted evidence
when a plan changes and identify any real invalidation.

Before dispatch, record a reservation with a unique dispatch token, original
outcome ID, attempt, workspace/write set, requested route, and intended worker
name. Put that token in the worker contract and task name or launch receipt.
Immediately after dispatch, append the returned worker/process identity. A
reservation without a returned identity means LAUNCH UNKNOWN, never pending work
that can be relaunched freely. On recovery, match it against live thread/process
inventory and artifacts using its token, workspace, and time. Establish either
that no launch occurred or that the corresponding writer is terminal before
releasing ownership. If visibility cannot resolve this, keep that write surface
blocked while continuing disjoint work. This reduces duplicate-dispatch risk;
it is not an atomic transaction with the external agent runtime.

## Pilot and flow control

Start with one representative outcome that exercises the intended build/review
route and integration assumption. Require an early concrete artifact for ambiguous
or expensive work, generally within 15–20 minutes, adjusted to the task. These are
lead-selected checkpoints, not provider-enforced timeouts. A useful result can
be a reproduction, coherent diff with a focused check, or resolved interface.

After acceptance, report cost/latency and remaining uncertainty, then expand only
if concurrency reduces expected total completion cost or the user values its
speed. Pilot acceptance is the lead's operational decision, not a new user gate.

Default to one active builder and at most two after a successful pilot. These are
tunable operating defaults, not hard runtime limits. Keep a reviewer slot and
enough capacity for repair/closure. Parallel recon is useful only when independent
questions will change decisions. Stop adding work when more than one coherent
candidate waits for review or integration cannot keep up.

Pause new fan-out after two failures with a shared cause across outcomes. Correct
the common assumption, harness, ownership, or routing before another wave. After
two failed attempts at one outcome, make a cause-based lead recovery decision.
Retries count across renamed tickets and sessions. A recovery is not evidence of
progress until it resolves a failed criterion.

## Cost and completion checkpoints

Apply [productivity.md](productivity.md) for review reservations, explicit stop
conditions for investigation, and time-based lead intervention. Its guard is a
review-counter helper, not a replacement for this run record or a project guard.

At the first accepted outcome, material failure, forecast change, and each milestone,
report accepted/total original outcomes, current work, review backlog, failed
attempts, elapsed time, and known usage. Distinguish observed charges, estimates,
and unavailable subscription quota. Avoid implying that a fixed amount of free
allowance remains because a CLI is logged in.

If no original outcome completes over two planned checkpoints, stop new dispatch
and examine whether the program is overlarge, fragmented, missing proof, or blocked
by integration. Consolidate or make a cause-bounded takeover as appropriate. If verification/lead
coordination dominates several comparable units, change the process before the
next wave. Do not continue buying review after all required claims are resolved.
The pause is for a concrete lead disposition, not a new planning project. Continue
independent ready work once the disposition is recorded; keep blocked dependencies
unfinished. Don't spend another hour rewriting orchestration documents.

Reserve the last part of the authorized envelope for assembled verification,
repairs, and handoff. When an explicit user cap is reached, stop billable dispatch
and provide the current artifact and missing gate. Do not invent a dollar ceiling
or promise enforcement when telemetry/runtime controls cannot enforce one.

## Goal continuation

An existing `/goal` retains its objective, scope, and acceptance rules. Advance it
through the runtime's provided mechanism; don't create another goal because the
skill was invoked. Mark completion only after all required outcomes and gates
are satisfied. Follow runtime rules for blocked status and budgets exactly.

A missing permission, credential, external state, or user-owned design choice can
block a dependency; a bad ticket or difficult decomposition is the lead's work.
Exhaust safe in-scope alternatives and continue independent authorized work while
waiting. Report the exact needed decision without rediscovering approvals already
given. Do not route around policy refusals or authorization limits.

## Context and crash recovery

Write the compact checkpoint before context becomes scarce and at every milestone.
Preserve paths, revisions, original criteria, accepted evidence, live worker IDs,
attempt history, authority, and the next executable step. Keep bulk logs out of
the handoff and point to them. Do not claim compaction creates independent review.

After restart or model change, inspect the checkpoint, current status/diff, and
live workers before dispatch. Reconcile stale reports against artifacts. If a
worker may still write, establish terminal state before replacing it. Never
blindly clean a dirty tree. Re-probe a changed model/transport only as needed.

## Terminal reconciliation

Close the original criteria, assembled behavior, required review, all processes,
and the final repository state. Report accepted work separately from pending
merge, deploy, live read-back, or owner decisions. Produce a useful handoff when
an external gate prevents completion; do not call the whole sprint finished.
