# Proportionate independent verification

## Decide the verification boundary before building

| Change | Required assurance |
|---|---|
| Pure formatting, comment, or inert copy change | Lead diff inspection and relevant cheap checks; self-reviewed is adequate |
| Meaningful logic, architecture, or agent workflow | Focused behavioral checks plus one fresh independent review at the coherent change boundary |
| Security boundary, money, migration, destructive behavior, subtle concurrency | Frontier independent review plus direct evidence of the relevant risk and recovery behavior |

Do not classify executable configuration, a workflow skill, or authorization
instructions as inert documentation just because the extension is Markdown/YAML.
Batch tightly related low-risk edits under one review contract. Keep distinct
high-risk ownership and proof boundaries. Every meaningful changed behavior
must be covered; batching is not an exemption from independent review.

For a substantial plan, request an independent challenge before broad implementation:
missing user promises, architectural failure modes, critical dependencies, overlarge
or fragmented tickets, absent proof, and credible cost traps. Do not require a
panel or repeated approval for every routine plan adjustment.

## Reviewer contract

Give a fresh reviewer the original user request, product criteria, baseline and
candidate identity, changed paths/diff, and allowed checks. Withhold builder claims,
the lead's preferred verdict, prior reviewer conclusions, and repair narratives
on its first independent pass. For a repair verification, it may receive the
reproduction and affected criteria; label that as targeted re-verification.

Ask it to derive the expected behavior first, inspect the implementation and
adjacent interaction paths, then verify the criteria. Require for each finding:
location, concrete trigger, violated promise, consequence, and reproduction or
reasoning. Label facts `OBSERVED`, code implications `DERIVED`, and untested
hypotheses `INFERRED`. Quotes and citations must resolve and support the claim.

A consequential plausible inference needs bounded investigation. A minor
unsupported preference is not a blocker. Neither reviewer confidence nor a
provider name determines severity. The lead adjudicates from evidence.

Have the reviewer state `PASS`, `FAIL`, or `INCOMPLETE`, criterion coverage, and
limitations. PASS means the assigned contract is supported, not that the entire
project is flawless. A missing required observation is INCOMPLETE, not a pass.
Readable evidence takes precedence over an exact first-line spelling.

## Candidate identity and independence

Freeze the review unit. Prefer a dedicated commit/worktree or isolated product
snapshot. Record the baseline, complete diff (including untracked product files),
candidate revision/content fingerprint, and dependencies. Keep prompts, logs, and
review artifacts outside the candidate. Do not hide relevant untracked changes
behind a clean tracked diff or assume ignored files are irrelevant.

For a reviewer with tool access, restrict writes where possible and compare
before/after product content. HEAD alone does not detect uncommitted mutation.
Separate generated test/cache outputs from source. A source mutation invalidates
the affected verdict; preserve the evidence, reconcile the mutation, and verify
the resulting candidate. The reviewer must never silently become a fixer.

Fresh context is independence from builder reasoning, not proof of a different
model or a secure sandbox. Same-model independent context is acceptable when it
clears the task's bar; disclose the distinction. If independent review is unavailable,
continue safe implementation/checks but label it SELF_REVIEWED or REVIEW PENDING.
Do not report a required independent gate as passed or ship a risky change under
reduced assurance without the user's authority.
Where independence is required, accepted completion remains pending until a
qualified fresh route checks it or the user explicitly accepts reduced assurance.
Distinguish finished implementation and local checks from that remaining gate;
an unavailable reviewer is not evidence the implementation failed.

## Economical proof sequence

1. Check ownership and the actual diff.
2. Run focused deterministic behavior, static checks, and relevant negative cases.
3. Review the coherent change independently; reproduce disputed claims.
4. Repair all substantiated in-scope findings together. Check affected behavior
   independently, with a wider boundary only when the impact analysis warrants it.
5. At assembled milestones, run required repository gates and the user's actual
   path: browser interaction, data read-back, or external observation as applicable.

Independent review may itself run the checks; the lead need not repeat every
identical passing invocation. Deterministic failure outranks a model PASS.
Record flaky results honestly and investigate them without an unbounded rerun loop.

Reuse evidence only while its candidate inputs and relevant dependencies remain
unchanged. Record what changed, which criteria depend on it, and why the rest is
unaffected. Interface changes, shared test fixtures, migrations, or environment
changes may invalidate much more than the changed lines.

A full final check is for the assembled user outcome, not ceremonial re-review
of every accepted slice. If the last independent review already covers the exact
assembled candidate and all original criteria, reuse it instead of buying another.

## Lead acceptance

Reconcile every original promise to an evidence artifact and disposition. Review
the diff and consequential findings yourself; personally check critical
user-facing or integration behavior, material gaps, and the highest-risk or
disputed observations when needed. Do not duplicate every passing command solely
because a worker or reviewer ran it. Audit routing and process closure separately
from product proof. Do not ask a blind product reviewer to certify hidden dispatch
history. Close all writers and required reviews before final acceptance.

Use ACCEPTED only for the scope actually supported, SELF_REVIEWED when that is
the assurance, NEEDS FIX for an in-scope defect, and BLOCKED for an actual missing
external dependency or authority. Report review-pending work as unfinished.
