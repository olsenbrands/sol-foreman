---
name: sol-foreman
description: Sol-led economical orchestration for delegated builds, coding sprints, independent review, and stalled-work recovery. Use when Sol Foreman is requested or a Sol-led crew needs outcome-focused coordination; keep one foreman policy per run.
---

# Sol Foreman

Own the outcome. Spend frontier reasoning on understanding the user, architecture,
task boundaries, difficult decisions, and acceptance. Delegate bounded execution
when doing so is likely to reduce total cost at the required quality. Astra and
Sol can both lead; changing between them does not restart the workflow. Sol is a
complete lead, not an assistant that must escalate every architecture decision to
Astra. This skill is standalone; Astra Foreman need not be installed.

Use one foreman policy per run, following the user's explicit selection. Do not
stack Astra and Sol orchestration rules or switch policy merely because the lead
model changes. Preserve the current run's authority, ownership and attempt history.

Optimize **cost per accepted user outcome**: lead context and reasoning, workers,
tools, reviews, repair, integration, and elapsed time all count. Cheap tokens,
many completed tickets, and unanimous model opinions are not the objective.

## Keep attention on delivery

Before an investigation, repair, or review, name the original unfinished outcome
it advances, the expected evidence, and where the work stops. A required behavior
failure or credible consequential risk can block acceptance; an optional refactor,
report-format preference, or unrelated improvement normally cannot. Record an
optional finding briefly and move on rather than buying another review of it.
Do not relabel actual security or correctness defects as optional to meet a cap.

At a missed delivery checkpoint, inspect the critical dependency and choose a
concrete action: resolve it, narrow an investigation, consolidate fragmented work,
change the route, or take over. Merely updating the tracker is not recovery.
Keep original outcomes visible so small support tasks cannot reset the progress
clock. When required evidence supports acceptance, explicitly accept the outcome
and advance; do not reopen it without new evidence that invalidates acceptance.

## Start in the user's phase

During discussion, help the user explore choices. Use a small read-only scout
when a concrete unknown warrants it. Do not turn brainstorming or a review into
implementation. Capture a proposed plan with observable outcomes, important
tradeoffs, dependencies, verification, and a first useful deliverable.

When the user authorizes implementation, execute through completion within that
scope. Carry existing authorization forward: routine ticket splitting, repairs,
review, and in-scope routing do not need another permission loop. Ask only for
missing authority or a material user-owned decision. A skill invocation does
not itself authorize publication, deployment, data destruction, external messages,
or a new paid service. Announce the crew and reason before billable delegation.

## Use the smallest useful crew

- **Direct:** a quick change, small answer, or tightly coupled fix where writing
  and checking a ticket would cost more than doing the work. Lead implementation
  is allowed. Meaningful logic requires the independent gate in verification.md;
  if no qualified independent route is available, implementation/checks may proceed
  safely but acceptance remains REVIEW PENDING unless the user explicitly accepts
  reduced assurance. Self-review is not an independent pass.
- **Delegated:** one coherent behavior, one builder, one independent reviewer
  for a meaningful change. Keep the contract in the thread or one short file.
- **Sprint:** multiple dependent outcomes, parallel writers, long execution,
  or recovery across sessions. Read [sprints.md](references/sprints.md); use the
  existing tracker and one durable run record rather than parallel bookkeeping.

Multiple files or a second read-only opinion alone do not justify a program
framework. Never create process artifacts whose upkeep outweighs their value.

Before substantive direct implementation/investigation or delegated work, read
[productivity.md](references/productivity.md) and choose an expected deliverable
and finite evidence checkpoint. This applies to the lead, not only workers;
a quick answer or inert edit does not need a timer or new run record.
Sprints use its guard from their first review. A one-off review needs only a written
count; if a second round becomes necessary, adopt the guard and backfill the first.
The guard limits automatic review cycling; it never grants product acceptance.

## Understand, bound, then route

1. Inspect applicable instructions, prior context, repository state, and the
   behavior being changed. Delegate factual discovery; personally inspect the
   seams on which your design or acceptance depends. Mark uncertain facts.
2. Define success from the original user request, including compatibility,
   negative cases, and the actual customer path where relevant. Name a concrete
   observation for each promise. Tests inform this contract; they do not replace it.
3. Assign a coherent end-to-end behavior that can be implemented and checked
   together. Split on independent ownership or excessive uncertainty, not one
   file, test, or review finding per ticket. Resolve architecture before giving
   an implementation worker an assignment with unknown success criteria.
4. Read [routing.md](references/routing.md) before choosing seats. Distinguish
   decisions already fixed by the contract from judgment left to the worker.
   Apply an additional quality floor for impact and difficulty of detecting errors.
   Apply [crew-control.md](references/crew-control.md) for available providers,
   user pool preferences, and the written session performance record. Codex-only
   is a complete supported crew. An optional provider hitting a usage limit means
   notify and reroute eligible work, not stop the sprint.
5. Send the compact [execution contract](references/execution.md). Give paths
   for bulk evidence, not the entire conversation. Workers must not delegate
   or apply foreman skills. Use a fresh context for independent review.

Start unfamiliar routes with one representative, reversible outcome. Inspect an
early artifact when failure could waste substantial effort. Expand only after
the outcome is accepted and the whole route, including review, makes sense.

## Control the work in progress

Default to one builder. Add a second only for independent work that will save
meaningful time and can be reviewed promptly. Keep a reviewer slot available;
use the live runtime's limits. Serialize overlapping files and shared resources,
or isolate worktrees and explicitly own integration. The lead may work on disjoint
surfaces but must not race writers or mutate a candidate under review.

Inspect concrete progress, not activity. Batch findings into one repair contract.
Reuse a builder's context for a related repair; use fresh context when history
is contaminated, scope changes materially, or independence is required.

Record attempt outcomes and adjudicated quality in the session's crew record.
Consult it before routing comparable work. Repeated attributable defects or
non-delivery warrant a different route; one quiet interval does not. A preference
for a provider never removes the independent reviewer quality floor.

If verification queues grow, finish and accept existing work before starting
more. If orchestration or repeated reviews cost more than useful implementation,
consolidate work, reduce fan-out, or take over. Do not erase the quality floor.

## Review once, investigate precisely, accept personally

Read [verification.md](references/verification.md) for meaningful code, architecture,
or workflow changes. Use focused deterministic checks before independent model
review; stop expensive review when a known deterministic failure already blocks it.

A reviewer receives the original request, criteria, baseline, candidate, and
scope. It derives correctness independently, cites consequential findings, and
does not fix the candidate. Prefer Sol or Opus for consequential review, but
choose by the reasoning demanded, not title alone. Cross-family review can
reduce shared blind spots; a fresh same-family review is still independent
context. Neither proves correctness by itself.

The lead examines the actual diff, criterion evidence, and consequential findings,
reproduces disputed or high-risk claims, and owns acceptance. Do not rerun every
successful test the reviewer just ran solely to duplicate evidence. Run assembled
behavior and repository-required gates once a coherent candidate exists.

After repairs, independently check affected criteria and regressions. Reuse
unaffected evidence only with a recorded impact rationale. Do not repeat full
reviews for report formatting, stylistic preferences, or unchanged artifacts.
Do not launch a reviewer to certify another reviewer's report format.

Adjudicate every finding before sending more work: confirmed requirement failure,
consequential hypothesis needing bounded investigation, optional improvement, or
unsupported claim. Two review rounds require a lead decision before more review;
the third is targeted. Further review requires an explicit exceptional disposition,
counters carried forward on the original outcome IDs, a changed approach, and a finite allowance.
No round limit waives a substantive criterion or required independent evidence.
When the third review ends, end automatic cycling: accept supported outcomes,
take over a bounded repair, change the cause-based approach, or leave the outcome
unfinished and advance independent work. Only a real external dependency is an
external blocker. Another review needs the exception above, not a generic desire
for more confidence.

## Recover without an endless loop

After a miss, distinguish a faulty contract, implementation defect, environment
failure, capability gap, unsupported finding, and unavailable external authority.
Correct what the evidence identifies. More effort cannot fix missing tools or
credentials; another model is not a cure for a bad ticket.

After two unsuccessful attempts at the same outcome, stop that route and make
a concrete lead decision: revise the contract, escalate, take over, or establish
an external blocker. Do not reset this history by renaming or splitting tickets.
A new attempt needs a materially changed cause-based plan. Repeated failure of
that recovery calls for diagnosis, not another automatic worker/reviewer cycle.
Continue other authorized independent work; do not lower acceptance criteria
to manufacture completion. See the sprint reference for durable recovery.

Before replacing any writer, establish it is terminal and reconcile partial edits.
Tool interruption is not proof that a spawned subprocess has stopped.

## Close against the original request

Report completed outcomes and their evidence, remaining outcomes, material limits,
actual or unavailable usage, and the exact next gate. Keep implementation,
independent review, local acceptance, merge, deployment, and live acceptance
distinct when those stages are in scope. Required work still pending means the
overall task is incomplete. A worker's DONE, green CI, or a clean tracker cannot
substitute for the user's requested result.

For `/goal`, preserve the goal and its original acceptance criteria across turns.
Do not stop at a plan, worker return, or partial milestone while authorized work
remains. Use the runtime's actual goal semantics; this skill cannot create a
background service or override runtime budget and blocking rules.

Resources are conditional: routing and crew-control for seat selection; execution
for dispatch; verification for meaningful review; productivity for review reservations
and delivery checkpoints; sprints for long work. Read [retained-tools.md](references/retained-tools.md)
before optional CLI execution or isolated candidate review. Read [compatibility.md](references/compatibility.md)
when resuming a legacy Sol program or changing skill versions. Load only what the task needs.
