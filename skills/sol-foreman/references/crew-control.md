# Available crew, preferences, and adaptation

## Select an eligible route, then apply preferences

For each role, apply this order:

1. User authority and hard restrictions, required tools/data access, available
   account/model/transport, and any spending cap.
2. Task-specific capability and impact floor; reviewer independence and eligibility.
3. User preference for provider/model allowance use among qualified routes.
4. Comparable observed quality, delivery reliability, total cost, and latency.

Quality evidence can disqualify a route at step 2. A pool preference cannot make
an unreliable or underqualified route eligible. Default routing tables are starting
points; they must not override a user's preference between qualified candidates.

Treat "emphasize," "favor," "mainly," and "use my remaining allowance" as soft
preferences for this session/run unless the user specifies a duration. Treat
"only," "never," and explicit caps as hard constraints. Record the interpretation
briefly and proceed; don't demand exact magic phrases or a configuration file.
A user-reported balance is usable preference evidence, not verified billing telemetry.
If the user changes priorities, record the new priority and apply it to subsequent
work; don't cancel productive active workers simply to rebalance providers.

- "Emphasize Grok": favor qualified Grok implementation/recon, with one representative
  pilot if that route is unfamiliar. Reserve Sol or Opus for consequential independent
  review. Grok may add advisory findings; a pool preference cannot promote that
  advisory lane into the required accepting review or replace it.
- "Use Claude allowance": favor Sonnet for suitable builds and Opus for consequential
  review. Use distinct builder/reviewer contexts even within one family.
- "Mainly Codex today": favor Luna for factual/mechanical tasks, Terra for bounded
  builds, and fresh Sol for consequential review, keeping the Astra/Sol lead.

Apply model-specific preferences only to eligible roles. Do not spend a premium
model on busywork merely to consume expiring allowance. If a hard restriction
leaves no qualified reviewer, report the conflict and keep review pending; never
relax the requirement silently. The lead's final acceptance is always separate.

## Supported account combinations

Codex is the complete baseline. Claude and Grok are optional; no signup or external
CLI installation is required to use the skill with Codex alone.

| Available and authorized crew | Suitable builders/recon | Consequential independent review |
|---|---|---|
| Codex only | Luna/Terra; stronger Codex when required | Fresh Sol, or fresh Astra if Sol unavailable and authorized |
| Codex + Grok | Eligible Codex or Grok; apply user preference | Fresh Sol/Astra |
| Codex + Claude | Eligible Codex or Sonnet; apply user preference | Fresh Sol/Astra or Opus |
| All three | Eligible routes from all three | Fresh Sol/Astra or Opus |

These examples presume the particular models are available. Discover exact
models/efforts from the runtime; map the role to another qualified available
Codex model if needed. A Codex account alone does not guarantee every model or
subagent tool. If no independent execution surface is available, disclose review
pending/self-review under verification.md; do not claim an independent pass.
Family diversity is useful when available, never a requirement for Codex-only use.

## Rate and usage limits: notify, reconcile, continue

Maintain a small availability table with provider/account route, model/transport
scope, state, evidence timestamp, reason, and next eligible retry/reset when known.
Useful states: AVAILABLE, TEMPORARILY LIMITED, EXHAUSTED, NOT CONFIGURED,
AUTH REQUIRED, and UNKNOWN. Keep account identifiers private. A model-specific
failure does not establish that the entire provider is unavailable.

When Claude or Grok reports a limit, tell the user the observed limit and new route
without asking them to approve ordinary fallback. Preserve the original contract,
partial artifact, review requirements, and attempts. Verify the old writer is
terminal and reconcile edits before replacement. Continue with already-authorized
qualified Codex models, retaining another available preferred provider if useful.
Claude limited plus Grok available therefore leaves Codex + Grok; both optional
providers limited leaves Codex-only. Do not wait for a reset while qualified
available capacity can advance the task. Apply the same rule if a reviewer hits
a limit: reroute the review in fresh context, never substitute builder approval.

Classify actual error evidence. A transient request/concurrency limit can justify
reduced concurrency or one bounded retry respecting provider retry guidance if
that is cheaper than migration. Known exhausted allowance goes directly to fallback.
An unknown error is not evidence of exhaustion; choose a known working route while
retaining that uncertainty. Do not poll an exhausted provider on every ticket.
Recheck at a known reset, a meaningful later checkpoint, or user report of restored
capacity; require fresh evidence before returning it to AVAILABLE.

Limits are availability events, not coding-quality failures. Keep their costs and
wall time in total run accounting. Missing permissions and policy refusals remain
authority/safety boundaries, not quota events to route around. If every qualified
authorized route is unavailable, continue any safe independent work and report the
remaining blocker. The skill cannot keep an unavailable primary session running.

## Written performance record

Before the first delegated dispatch, create a compact crew section in the existing
run record or `.foreman/<run-id>/crew.md`. For a read-only task use a private task
directory outside the target repository. Tell the user its path. This is required
even for a small delegated session, but one row is sufficient; do not initialize
a whole program framework. The lead alone writes it. Keep it out of publication.

For ordinary work, one compact durable entry suffices: original outcome/attempt,
route (model + effort + tools + task fit), worker identity/write scope, checkpoint,
result/evidence, adjudicated defect or cause, independent reviewer and usage or
unavailable. Fold the routing hypothesis into that entry. Update it at dispatch,
material problems and closeout; do not build summary tables or calculate statistics
for a single task. Keep prior attempts when updating the current state.

For sprints or repeated comparable tasks, extend that same record as useful with
the structure below; do not require every field or duplicate equivalent records:

```text
Preference: original wording; interpretation; scope/expiry; timestamp
Availability: route | state | evidence/time | retry/reset or unknown
Attempts (append observations/corrections; retain original outcome IDs):
  outcome/attempt | role/task-shape/risk | candidate/contract | worker identity
  requested/served model + effort | CLI/tool environment | start/checkpoint/end
  result/coverage | adjudicated defects + evidence | cause | reviewer identity
  worker time / external wait / review+repair time | usage/cost or unavailable
Summary by comparable role/task-shape/model/effort/environment:
  completed/assigned; first-pass accepted/evaluable; incomplete/pending;
  attributable substantive failures; non-delivery episodes; time-to-acceptance;
  observed review false positives/misses; sample size and uncertainty
Routing decisions: old route -> new route | cause/evidence | next observation
```

Update at dispatch, a material checkpoint problem, report, review adjudication,
and acceptance. Consult the record before the next comparable dispatch and after
compaction/restart. Link raw proof instead of copying transcripts. Reuse run records
across the same sprint's sessions; a new unrelated run starts a new record. Prior
records may inform a prior when explicitly available, but don't silently create
global memory, provider policy, or an account-wide reputation database.

Evaluate the delivered artifact and required behavior, not activity or confident
reports. Count substantive defects after lead adjudication, not all reviewer
complaints. Record reviewer performance too: supported/actionable findings, rejected
claims, and consequential misses discovered by later independent evidence. Lack
of discovered misses does not prove perfect recall. Don't reward finding volume.

Attribute causes: contract ambiguity, missing context, implementation defect,
capability gap, tool/environment failure, quota, and non-delivery. A deliberately
cancelled task, blocked credential, or pending review is not a model-quality failure.
Retain those rows and excluded counts so statistics cannot hide failures or spend.
Use first-pass acceptance only over outcomes with adjudicated first attempts;
report numerator/denominator and pending cases. Record wall time to acceptance
separately from worker execution and external waits. Unobserved timing is unknown.

## Adapt with evidence and restraint

Before dispatch, write a short route hypothesis in the crew record: task type and
risk; model/effort/tools; why it should fit; first expected artifact and checkpoint;
signals for keeping or changing the route. For example: "Terra/high/native tools,
bounded API contract; first request-path test at 15 minutes; inspect environment
failure before changing model, change route after repeated attributable omissions."
Consult this hypothesis and comparable evidence at checkpoints and before the next
similar task. Record keep/change plus reason; do not recalculate a leaderboard on
every tool call. Change one major factor where practical and preserve uncertainty.

An idle UI indicator or silence alone is not failure. At a missed agreed artifact
checkpoint, inspect process state, tool wait, and latest artifact; send one focused
status/checkpoint request if needed. Allow a task-appropriate response window.
If it is still progressing, adjust the forecast rather than interrupting it. Repeated
missed checkpoints with no useful artifact, or repeated terminal non-delivery,
warrant reconciliation and a different worker/route; don't leave silent work open
indefinitely. Establish terminal state before replacement.

After repeated comparable, attributable defects or non-delivery, review the
contract and environment first. Use two such attempts as a decision checkpoint,
not statistical proof a model is bad. Change model, effort, tool environment, or
task boundary according to the diagnosed cause. Serious unsafe/scope behavior can
justify immediate intervention; no need to accumulate two incidents. Preserve the
original outcome's retry history and apply the main skill's recovery limits.

Give an alternative qualified route one useful bounded task with the same quality
bar, then compare accepted completeness and total repair/review burden. Change one
important factor where practical; record confounders. Prefer local statements like
"route A has two incomplete API-contract tasks at this effort" to global model
rankings. Avoid raw rejection-rate rankings across different risk/task mixes,
unearned numeric scores, or benchmark races unrelated to the user's work. Sparse
observations remain tentative; model/tool updates can invalidate old conclusions.
