# Productive completion and bounded review

## Keep the next action connected to delivery

Before another investigation, repair, or review, identify the original criterion
or delivery blocker it advances, the evidence expected, and the stopping condition.
One sentence in the run record or ticket is sufficient. If there is no connection,
defer the work. A real newly discovered risk can warrant investigation; explain its
consequence instead of silently enlarging the original acceptance contract.

Track accepted original outcomes and the current critical dependency, with pending
review, repair time, and scope growth. Supporting artifacts matter but do not count
as finished deliverables. A small test-only ticket must not reset the time since
the last original outcome completed. Don't game throughput by cherry-picking tiny
items while the required integration path remains stuck.

## Checkpoints that require decisions

Choose expected outcome duration and evidence checkpoints before substantive direct
work as well as dispatch. Lead investigation and implementation count against the
same original delivery clock; delegate-only monitoring misses lead fixation. These
defaults are operational heuristics, not model benchmarks or automatic timeouts:

| Trigger | Required lead action |
|---|---|
| First artifact, generally 15–20 minutes | Inspect reproduction, working path, or coherent diff; decide whether the route is on course |
| Two missed agreed artifact checkpoints | Inspect tools/process and artifacts, request a bounded status response, then redirect or replace if no useful progress |
| Two review rounds | Adjudicate all remaining findings before any further review |
| Third review | Assign only named unresolved criteria and affected regressions, with an explicit stopping observation |
| Third review ends | End automatic cycling and record acceptance, takeover/repair, approach change, or an actual blocker |
| No original outcome accepted for roughly 45–60 minutes | Inspect the critical path, scope, verification overhead, and lead takeover option before dispatching more |

Long tests, migrations, research, or large coherent outcomes can need longer
milestones. Set justified alternatives before dispatch. If evidence later changes
the estimate, document the actual artifact and cause; do not repeatedly move the
deadline merely because it expired. Useful progress may justify continuing, but
the lead must name the next artifact and finite checkpoint. Check elapsed time at
tool/control boundaries; this skill cannot wake a suspended session autonomously.

When a checkpoint fails, choose a concrete action: narrow an overlarge behavior,
consolidate fragmented tickets, repair the contract/environment, change the route,
finish the coupled work directly, or establish an external blocker. Do not respond
with another open-ended audit or generic replan. Keep previous writers terminal
before replacement. Preserve accepted evidence and progress independent work.

## Lead adjudication, not reviewer unanimity

Classify each finding when it arrives:

- Confirmed criterion violation: fix and check the affected behavior.
- Consequential hypothesis: assign one bounded reproduction/investigation.
- Optional improvement: record owner, reason for deferral, and promotion trigger.
- Unsupported/incorrect claim: dismiss with evidence.

Reviewers do not expand the contract by expressing preferences. A material newly
discovered correctness or safety issue can still block acceptance. Batch confirmed
repairs; do not buy one full review per finding. Independent re-verification can
be narrow when its impact rationale is sound. A live contradiction needs resolution,
not more votes. When all required criteria and independent gates have evidence,
the lead accepts; unanimous reviewers and speculative perfection are unnecessary.

After the ordinary review allowance, the lead still owns judgment. It may accept
only when required evidence supports acceptance, take over a fix, change the
approach, or mark the outcome unfinished while advancing independent work. An
exceptional additional review may be warranted for changed implementation or
unresolved material risk. State what changed and the exact question; do not reuse
"quality assurance" as a perpetual override. Budget/round exhaustion never converts
a known defect or missing required independent proof into PASS.

## Review dispatch guard

For sprints, reserve every delegated product/plan review through
`scripts/review_guard.py`, resolved relative to this skill. For a one-off review,
record its count in the crew note; adopt the guard before any second round and
backfill the first. Python 3 standard library only. Reuse one database for the
same original goal across sessions; keep it private beside the run record. Register
the original outcome IDs once. Newly authorized scope uses `add-outcomes` with a
recorded authorization reason; existing IDs cannot be added again. Do not reset
existing work by presenting a split or renamed ticket as new scope. Do not reset counts by changing ticket names, making
a fresh database, splitting work, or labeling a review as recon. A review round is
one reserved model review call/context, including a substantive reviewer follow-up.
Record `--kind plan` for architectural plan challenge and `--kind product` for
implementation review AND re-verification. Each kind has its own escalation ladder,
while the guard retains total reservations across both. A normal plan challenge
followed by a product review and one repair check is plan round 1, product rounds
1 and 2. Never reclassify a repair check as plan/recon to escape the ladder.
Routine lead triage and deterministic tests are not model review rounds. Genuine
fact-finding without a review verdict is recon, with its own evidence checkpoint.

Example (replace paths and outcome IDs with the actual run contract):

```sh
python3 /path/to/skill/scripts/review_guard.py init /path/to/run/reviews.db --outcomes ITEM-1 ITEM-2
python3 /path/to/skill/scripts/review_guard.py reserve /path/to/run/reviews.db --outcomes ITEM-1 --kind product --ticket T1-review --criteria PC-1 --purpose 'Check the changed request path' --expected 'Negative and success behavior match PC-1' --minutes 20
python3 /path/to/skill/scripts/review_guard.py finish /path/to/run/reviews.db --reservation 1 --result pass --evidence /path/to/review-report.md
python3 /path/to/skill/scripts/review_guard.py status /path/to/run/reviews.db
python3 /path/to/skill/scripts/review_guard.py add-outcomes /path/to/run/reviews.db --outcomes ITEM-3 --reason 'User authorized the additional export behavior'
```

Dispatch only after a successful reservation. Copy its ID into the crew record
and bind the returned worker identity there immediately after launch. A batched
review reserves every original outcome it covers, atomically. Within each kind, rounds 1–2 use the
ordinary arguments. Round 3 also requires `--decision` and `--changed-approach`;
round 4 onward additionally requires `--exception 'specific justification'`. These fields record the lead's
in-scope judgment, not a new user-approval requirement. Every reservation requires
criteria, purpose, expected evidence, and positive finite minutes.

Finish after the worker is terminal and its evidence is collected. `pass`, `fail`,
`incomplete`, and `not-started` describe the review attempt, not product acceptance.
Use `not-started` only with evidence that no launch occurred. A reservation whose
launch result is unknown stays active until lifecycle reconciliation resolves it.
Counts are reservations, including failed/no-launch attempts, not claimed billable
calls. Record actual launches and quota incidents separately for cost/quality data.
When adopting the guard mid-run, backfill known prior reviews using reserve/finish
with purpose and evidence explicitly marked as historical migration. Include the
round decisions required by the current rules. Guard timestamps then mean record
time, not original execution time. Preserve the earlier reports and any unknown
history; do not present a new database as proof that no earlier reviews occurred.
For a version-1 guard database, run `migrate` once. It preserves previous counts and
records, conservatively classifying historical reviews as product; it does not
retroactively refund rounds. Missing or malformed state must be reconciled, not
silently replaced. A failed new initialization must not overwrite an existing file.

The guard rejects unknown original IDs, overlapping active reservations, ticket
aliases moved to different outcomes, and missing round-decision fields. It records
history transactionally and has no product acceptance operation. It cannot evaluate
whether a reason is honest, observe worker termination, enforce minutes or spend,
or intercept direct native/CLI calls that bypass it. The lead must still obey
scope, elapsed-time, process-closure, and quality rules. A higher round number is
a signal of exceptional work within the same kind, never normal throughput.
`status` shows reservation time, elapsed minutes, and overdue status for active
reviews. These are observations for the lead, not automatic termination triggers;
reservation age includes any delay before the actual launch. Use the crew record
to distinguish execution time, waiting, and actual worker identity.

If Python or durable storage is unavailable, keep equivalent counts and decisions
in the written record, disclose that machine enforcement is unavailable, and
continue safe authorized work. Do not install new infrastructure or create another
guard system merely to process a small task. Existing repository guards remain
binding; this helper does not supersede them.

Bound diagnosis of helper failures; do not turn a small deliverable into an
infrastructure repair project. Manual accounting must preserve earlier counts,
active reservations and ownership uncertainty, never evade a valid guard denial.
