# Task contracts and durable state

## Contents

- [Derive criteria from the goal](#derive-criteria-from-the-goal)
- [Ticket schema](#ticket-schema)
- [Evidence and negative claims](#evidence-and-negative-claims)
- [Statuses and verdicts](#statuses-and-verdicts)
- [Parallel writes and ledger](#parallel-writes-and-ledger)
- [Retries and process closure](#retries-and-process-closure)

## Derive criteria from the goal

Write criteria before delegation. Start with the user's requested outcome, users/inputs affected, required behavior, compatibility promises, and forbidden outcomes. Turn each promise into an independently observable criterion and a stated observation method.

Do not derive criteria solely from existing tests, a worker plan, or the proposed algorithm. Tests are evidence, not the definition of success. Add a goal-derived behavioral criterion when tests omit an observable user promise. Do not make a criterion self-confirming by accepting the worker's own assertion as its only proof.

Maintain two separate sets:

| Set | Owner | Proves |
|---|---|---|
| Product criteria | Builder evidence plus a product verifier | The changed artifact satisfies the user's observable outcome. |
| Orchestration criteria | Lead audit, not the product verifier | The correct ticket, route, evidence provenance, scope, retries, independent-review boundary, and process closure occurred. |

Give a blind product verifier only product criteria it can inspect. Do not ask it to confirm hidden dispatch history or builder claims. The lead audits orchestration evidence separately and retains final acceptance.

## Ticket schema

Give every worker one bounded ticket:

    TASK: <bounded objective>
    GOAL: <user outcome and affected behavior>
    EXPECTED OUTCOME: <observable definition of done>
    CONTEXT: <paths, baseline, relevant supplied facts>
    ROUTING: <residual judgment, quality floor, lane, requested seat/effort, evidence label, uncertainty>
    PRODUCT ACCEPTANCE CRITERIA:
    - PC-1: <goal-derived, independently observable promise>
    - PC-2: <criterion>
    ORCHESTRATION REPORT REQUIREMENTS:
    - <evidence the worker must return; the lead owns audit and acceptance>
    VERIFICATION:
    - PC-1: <exact command, behavior check, or inspection and expected observation>
    EVIDENCE REQUIRED:
    - <approved raw stream/artifact path, diff, command result, timing/cost fields>
    CONSTRAINTS: <stack, compatibility, patterns, permissions>
    MUST DO: <non-negotiable requirements>
    MUST NOT: <scope fence, forbidden side effects, no subagent spawning>
    WRITE SET: <every permitted file/glob; omit only for read-only work>
    STOP CONDITIONS: <unsupported material fact => NEEDS_CONTEXT; environmental failure => BLOCKED with exact evidence>
    OUTPUT FORMAT: <worker status and required report fields>

Keep the original task and product criteria inline. Pass bulk context by path. State behavior and fences without needlessly prescribing an algorithm; when an algorithm is prescribed, say so in routing so residual judgment is assessed honestly.

Do not repeat `$sol-foreman`, tell an execution worker to use Sol Foreman, or
include another orchestration-skill trigger in its ticket. The lead has already
applied the skill. Repeating the trigger can make a repository-fenced worker
load orchestration material outside its read scope. Give the worker the
self-contained contract it needs instead. In `MUST NOT`, say that this is a
bounded execution role and it must not load or apply orchestration skills,
delegate, or read outside the supplied repository/context paths.

The lead creates a companion orchestration contract before dispatch:

    ORCHESTRATION ACCEPTANCE CRITERIA:
    - OC-1: <declared lane, requested seat/effort, and evidence labels are recorded honestly>
    - OC-2: <write-set isolation, baseline, and dispatch order are evidenced>
    - OC-3: <product verification is blind to builder narrative where independence is required>
    - OC-4: <all attempts, retries, final gates, and process closure are recorded>

Do not make a worker or product verifier certify this orchestration contract. The lead verifies it from the ledger, raw evidence, and process state.

## Evidence and negative claims

Require evidence that another reader can inspect without trusting a summary:

- exact command, working directory, start/end ISO 8601 timestamps, exit status, duration, and relevant environment/version;
- changed paths, diff or artifact location, and exact test or behavior observation mapped to each product criterion;
- approved raw event stream location and a redaction record when redaction is necessary; never persist secrets or raw account-auth payloads;
- requested model/effort plus every applicable evidence label and source, runtime usage/tokens/cache fields, billing mode, and provider-reported cost when available;
- baseline and final repository status, verifier before/after fingerprint where relevant, and explicit unknowns.

Make negative claims observable and bounded. For example, support "no writes outside WRITE SET" with a baseline/final diff and status; support "no worker remains" with process/thread IDs and a terminal-state check; support "no artifact in locations X/Y" with the searched locations, command, time, and visibility limit. Never replace a bounded observation with an absolute claim that cannot be observed.

Preserve raw evidence in an approved, access-controlled location. A report may summarize it, but the summary is not a substitute for the raw source. If cost, timing, runtime metadata, or a stream is unavailable, record `unavailable` with the reason rather than inventing it.

## Statuses and verdicts

Require the worker's first line to be exactly one:

| Status | Meaning | Lead action |
|---|---|---|
| `DONE` | Work is complete with required evidence. | Inspect artifacts and enter verification. |
| `DONE_WITH_CONCERNS` | Work is complete but risks or unverified items remain. | Resolve every concern before acceptance. |
| `NEEDS_CONTEXT` | A specific unsupported material fact prevents safe work. | Supply it and re-dispatch the corrected ticket. |
| `BLOCKED` | A capability or environment prevents completion. | Record exact evidence, classify, and escalate; do not pretend. |

Require the report after the status to include changed files, criteria-by-criterion observations, exact checks, raw evidence locations, model evidence labels, timing/cost/usage or `unavailable`, concerns, blockers, and repository status when it could write.

Require a verifier's first line to be exactly one:

| Verdict | Meaning |
|---|---|
| `PASS` | Every assigned product criterion was independently reproduced. |
| `FAIL` | A required criterion failed or lacks required evidence. |
| `PASS_WITH_NOTES` | All assigned criteria passed; notes are outside required scope. |

Do not mix worker statuses with verifier verdicts. A product `PASS` does not certify orchestration; the lead determines final acceptance only after both proof sets pass.

## Parallel writes and ledger

Before a wave, compare WRITE SET values. Treat manifests, lockfiles, generated output, migrations, and shared fixtures as overlap. Serialize overlapping tickets or isolate them in worktrees/copies; tell every worker the filesystem is live and forbid out-of-set edits. Snapshot the baseline. Read-only lanes may overlap only when they do not share an exclusive environment.

For authorized delegated repository-write runs, use `.foreman/ledger.md` with append-only entries:

    # Foreman Ledger — <task>
    BASELINE: <commit> | <status summary> | <timestamp>

    ## Plan
    <task graph, dependencies, final gates>

    ## Routing
    <task | residual judgment | quality floor | lane | requested seat/effort | evidence labels | uncertainty | reason>

    ## Tasks
    <id | lifecycle | write set | canonical process/thread identity | artifact path>

    ## Verification Contracts
    <id | product criteria/gates | orchestration criteria/proof owner | evidence required>

    ## Attempts
    <append-only: task | attempt | ticket revision | seat evidence | command | start/end | exit | duration | usage/cost | result | evidence>

    ## Process Closure
    <task | process/thread identity | terminal observation | time | remaining-writer check>

    ## Decisions
    <scope, consent, criteria corrections, route changes, uncertainty, blockers, acceptance>

Use `PENDING -> DISPATCHED -> REPORTED -> VERIFYING -> VERIFIED`, with `FAILED -> FIXING -> VERIFYING` for correction. Read-only advisory tasks may end `ACCEPTED`; solo work ends `SELF_REVIEWED`, never `VERIFIED`. For read-only work, keep equivalent state in the thread or permitted temporary location, not the target repository.

## Retries and process closure

Append attempts and decisions; never rewrite history to make a run appear cleaner. Apply the first matching rule:

1. Correct a bad ticket or unreasonable criterion and retry the same seat; record why it was not a model failure.
2. After a first real failure, add missing context/evidence or raise effort.
3. After a second real failure at one seat, escalate one capability class or let the lead take over.
4. Stop and report evidence after failure at the highest suitable seat.
5. Stop after two failed fix waves against the same findings.

Do not retry identical input a third time or downgrade after evidence proves a stronger seat is required. When a worker stops reporting, confirm whether it is live; interrupt only when necessary; record `LOST`, identity, last artifact, and exit information; diff against baseline; reconcile partial edits; and never start a replacement while the old writer may still be live.

Before final acceptance, record terminal state for every dispatched worker/process, inspect for remaining writers, reconcile partial artifacts, and re-run the full product and orchestration contracts.
