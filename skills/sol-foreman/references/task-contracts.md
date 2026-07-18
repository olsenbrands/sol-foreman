# Task contracts and durable state

## Contents

- [Ticket schema](#ticket-schema)
- [Worker statuses](#worker-statuses)
- [Verifier verdicts](#verifier-verdicts)
- [Parallel write rules](#parallel-write-rules)
- [Ledger](#ledger)
- [Failure precedence](#failure-precedence)
- [LOST workers](#lost-workers)

## Ticket schema

Give every worker one task:

    TASK: <bounded objective>
    EXPECTED OUTCOME: <observable definition of done>
    CONTEXT: <paths, baseline, relevant facts>
    ACCEPTANCE CRITERIA:
    - VC-1: <independently gradeable criterion>
    - VC-2: <criterion>
    VERIFICATION:
    - <exact command or behavior check mapped to criteria>
    EVIDENCE REQUIRED:
    - <diff, file:line, command output, screenshot, artifact path>
    CONSTRAINTS: <stack, compatibility, patterns, permissions>
    MUST DO: <non-negotiable requirements>
    MUST NOT: <scope fence, forbidden side effects, no subagent spawning>
    WRITE SET: <every permitted file/glob; omit only for read-only work>
    STOP CONDITIONS: <when to report blocked rather than guess>
    OUTPUT FORMAT: <status or verdict contract>

Keep the original task and criteria inline. Pass bulk context by path. Do not paste long logs, histories, or source files into a ticket.

## Worker statuses

Require the first line to be exactly one:

| Status | Meaning | Lead action |
|---|---|---|
| `DONE` | Work complete with required evidence | Inspect artifacts and enter verification |
| `DONE_WITH_CONCERNS` | Complete, but risks or unverified items remain | Resolve every concern before acceptance |
| `NEEDS_CONTEXT` | A specific missing fact prevents safe work | Supply it and re-dispatch the corrected ticket |
| `BLOCKED` | Capability or external condition prevents completion | Classify and escalate; do not pretend |

Require a compact report after the status:

- files changed and why;
- exact commands run and results;
- evidence per acceptance criterion;
- concerns, unverified items, and blockers;
- created artifact paths;
- repository status if the worker could write.

## Verifier verdicts

Require the first line to be exactly one:

| Verdict | Meaning |
|---|---|
| `PASS` | Every required criterion independently reproduced |
| `FAIL` | At least one required criterion failed or lacks required evidence |
| `PASS_WITH_NOTES` | All required criteria passed; notes are outside required scope |

Do not mix worker statuses with verifier verdicts.

## Parallel write rules

Before a wave:

1. Compare WRITE SET values.
2. Treat manifests, lockfiles, generated output, migrations, and shared fixtures as overlap.
3. Serialize overlapping tickets or isolate them in separate worktrees/copies.
4. Tell each worker the shared filesystem is live and forbid edits outside its set.
5. Snapshot the baseline.

Read-only lanes may run in parallel when they do not consume a required exclusive environment such as a shared test database.

## Ledger

Use `.foreman/ledger.md` for delegated repository-write runs when those writes are authorized:

    # Foreman Ledger — <task>
    BASELINE: <commit> | <status summary> | <timestamp>

    ## Plan
    <task graph and dependencies>

    ## Routing
    <task -> lane -> model + effort -> reason>

    ## Tasks
    <id | lifecycle | write set | agent/process id | artifact path>

    ## Verification Contracts
    <id | VC list | exact gates | evidence required>

    ## Attempts
    <append-only: task | attempt | seat | ticket revision | result | evidence | time>

    ## Decisions
    <scope, consent, criteria corrections, seat changes, blockers>

Use lifecycle states:

    PENDING -> DISPATCHED -> REPORTED -> VERIFYING -> VERIFIED
                                             \-> FAILED -> FIXING -> VERIFYING

Read-only advisory tasks may end at `ACCEPTED`. Solo-mode work ends at `SELF_REVIEWED`, never `VERIFIED`.

Append attempts and decisions. Do not rewrite history to make a run look cleaner.

For read-only assignments, do not create a ledger in the target repository. Keep equivalent state in the thread or a permitted temporary directory.

## Failure precedence

Apply the first matching rule:

1. **Bad ticket or unreasonable criterion:** correct it and retry the same seat; record the correction.
2. **First real failure at the seat:** add missing evidence or context, or raise effort.
3. **Second real failure at the seat:** escalate one capability class or have the lead take over.
4. **Failure at the highest suitable seat:** stop and report the evidence.
5. **Two failed fix waves against the same findings:** stop, even if other seats remain.

Do not retry identical input a third time. Do not downgrade a task after evidence proves it needs a stronger seat.

## LOST workers

If a worker or process stops reporting:

1. Confirm whether it is still running.
2. Interrupt or terminate it only when needed, then confirm terminal state.
3. Record `LOST`, process/thread identity, last artifact, and exit information.
4. Diff the tree against the baseline.
5. Reconcile partial edits before any retry.

Never launch a replacement while the old writer may still be live.
