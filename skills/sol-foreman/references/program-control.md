# Program control

Use this protocol only in program mode. A one-worker low-risk task uses the inline lightweight contract in `task-contracts.md`.

## Reconnaissance and sizing

Before implementation, freeze the baseline, applicable instructions and tracker, user-visible promises, repository-native gates, architecture seams, persistent/shared state, dependencies, write ownership, and true external blockers. Missing internal understanding requires bounded reconnaissance or decomposition, not `BLOCKED`.

One ticket should own one behavior, one coherent write surface, and one reproducible proof bundle. Preflight tripwires include more than five criteria, two subsystems, ten expected paths, two risk seams, three original program items, or sixty minutes. Recursive globs, root globs, drive-relative paths, compound labels, multiple stacked tripwires, and unresolved facts require decomposition. One isolated tripwire may proceed only with the script's lead override and an early artifact checkpoint.

Set risky-ticket checkpoints no later than twenty minutes or half the estimate. Require a concrete artifact: a minimal reproduction, first bounded diff plus focused gate, frozen interface, migration contract, or rendered interaction.

## Initialize guarded state

Create an explicit, unique registry of the original program items. The count and registry length must agree:

    {"schema_version":1,"event":"program_started","program_id":"P-1","plan_id":"plan-1","total_items":45,"program_item_ids":["ITEM-01","ITEM-02","...","ITEM-45"],"long_program":true,"pilot_limit":1,"max_parallel":3}

Use `long_program:true` above ten items and for hour-plus, multi-wave, or material migration/auth/payment/provider/concurrency work. Long programs require a one- or two-ticket pilot. Short program-mode work omits `pilot_limit` but still sets `max_parallel`.

Keep tickets, events, prompts, streams, and reports outside a product-only verifier candidate. The lead is the sole JSONL writer. Record non-dispatch events with:

    python3 "<skill-root>/scripts/program_guard.py" record <events.jsonl> <event.json>

Inspect state with `status`. Use `py` when that is the available Windows launcher.

## Dispatch and ownership

Every execution ticket includes `program_item_ids`: the original tracker items it advances. Supporting slices may later verify without completing an item; only explicit `completed_item_ids` count as accepted program progress.

Create a route manifest or native-session record, hash it, then dispatch only through:

    python3 "<skill-root>/scripts/program_guard.py" dispatch <events.jsonl> <ticket.json> --attempt 1 --worker-id <id> --provider <native-codex|codex-cli|claude-cli|lead> --model <observed-model> --effort <level> --route-evidence-sha256 <64-hex> --repo-root <absolute-workspace-root> --workspace-id <stable-worktree-or-copy-id>

The command reruns preflight, resolves existing filesystem aliases inside the named workspace, and binds the ticket digest, plan, dependencies, portable write identities, a privacy-local digest of the resolved workspace root, original item IDs, attempt, worker, provider, model, effort, and route-evidence digest. The guard refuses undeclared items, completed items, unverified dependencies, concurrent ownership of the same item, aliases into metadata or outside the workspace, case-alias or overlapping active/reported write sets, recursive/root/drive paths, duplicate attempts, more than three attempts, pilot overflow, and parallel overflow. Distinct isolated worktrees/copies use distinct stable `workspace_id` values; the root digest prevents relabeling one workspace to bypass overlap.

Write-set comparison intentionally uses case-insensitive portable semantics so tickets remain disjoint on ordinary macOS and Windows filesystems. Shared manifests, lockfiles, generated output, migrations, and fixtures are overlap even if a string comparison appears disjoint.

Read-only recon and advisory workers remain in the thread or ledger. `program_guard.py dispatch` records preflighted execution tickets, not read-only probes.

## Worker reports and independent acceptance

Worker `DONE` is only a report. Record its terminal outcome with a digest of the terminal CLI receipt or native-session evidence:

    {"schema_version":1,"event":"ticket_outcome","ticket_id":"T-1","attempt":1,"outcome":"reported","worker_receipt_sha256":"<64-hex>","worker_minutes":18,"noncached_input_tokens":12000}

For unavailable telemetry, omit the number and set `<field>_status:"unavailable"` plus `<field>_reason:"<why>"`. Non-finite values and invented zeroes are invalid.

After a different process/session reproduces the gates and the lead reviews evidence, record:

    {"schema_version":1,"event":"ticket_verified","ticket_id":"T-1","attempt":1,"verifier_id":"verifier-1","verifier_evidence_sha256":"<different-session-or-receipt-digest>","verdict":"PASS","lead_reviewed":true,"processes_closed":true,"verification_scope":"slice","completed_item_ids":["ITEM-01"],"criteria_evidence_path":"<artifact>","criteria_evidence_sha256":"<64-hex>","candidate_fingerprint":"<64-hex>","verification_minutes":4,"verification_noncached_input_tokens":2500}

`completed_item_ids` must be assigned to that ticket and may be empty for a verified supporting slice. A completed item can be counted once. A verified ticket is terminal; no later outcome or verifier failure can rewrite it. Builder/verifier identity comparison is case-insensitive, and verifier evidence must identify a different process or session.

When verification fails, record `ticket_verification_failed` with `verdict:"FAIL"`, lead review, canonical cause, finding evidence path/digest, candidate fingerprint, distinct verifier evidence digest, and telemetry. It returns the attempt to bounded recovery without completing an item.

## Pilot, reports, and projection

A long program admits no more than `pilot_limit` new tickets and always respects `max_parallel`. Fan-out remains frozen until a pilot both verifies and completes at least one original program item.

Copy the exact counters and entire `projection` object from `program_guard.py status` into `progress_reported`:

    {"schema_version":1,"event":"progress_reported","reasons":["first_verified","pilot_result","projection"],"snapshot":{"accepted_items":1,"verified_tickets":1,"attempts":1,"remaining_items":44,"active_attempts":0,"reported_unverified":0,"elapsed_minutes":24,"projection":{"remaining_items":44,"observed_work_minutes_per_completed_item":22.0,"projected_additional_work_minutes":968.0,"observed_noncached_tokens_per_completed_item":14500.0,"projected_additional_noncached_input_tokens":638000.0},"projection_note":"Projection is copied from guarded accepted throughput and observed usage."}}

The guard rejects fabricated projection values and decreasing elapsed time. Then record `pilot_approved` with substantive evidence. If the pilot produces only supporting slices or failures, correct it or report and replan; do not fill the backlog to look busy.

`max_parallel` bounds active plus reported-but-unverified outstanding work, so a completed worker does not free capacity until verification resolves it. Verify reported work before dispatching another wave. Report after the first verified ticket, first unsuccessful result, breaker, full verification backlog, attempt exhaustion, material forecast change, and all original items completed.

## Breaker and replan

Canonical cause families are `oversized-ticket`, `bad-ticket`, `capability-gap`, `implementation-defect`, `verification-harness`, `shared-ownership`, `external-dependency`, `flaky-evidence`, and `unknown`.

Two distinct `needs_fix`, `rejected`, or `parked` tickets in the same cause family halt dispatch. Report the exact state and projection, diagnose the shared cause, and record a substantive `replanned` event. Replan is also legal after a pilot, a three-attempt unit, or any terminal parked unit exhausts.

Every active writer and reported attempt must reach terminal review before replan. No replacement can overlap an old-plan worker hidden from the current plan. Every long-program replan returns to a new pilot.

## Retry ladder

After a failed attempt, record `recovery_action` before retrying:

    {"schema_version":1,"event":"recovery_action","ticket_id":"T-1","after_attempt":1,"action":"add-evidence","evidence":"Attach the exact failing command and smallest reproducing diff."}

Allowed actions are `correct-ticket`, `add-evidence`, `raise-effort`, `escalate`, and `lead-takeover`.

1. Correct a bad ticket, false assumption, or harness defect.
2. Add the smallest missing evidence or raise effort.
3. Attempt three requires a different worker, a changed provider/model/effort route, and a different route-manifest digest, or a distinct `lead` takeover route. The lead must establish that the change raises capability rather than merely changing labels.
4. A third `needs_fix` or `rejected` result creates `attempt_exhausted`. Any `parked` result is terminal and also creates `attempt_exhausted`. Report and replan the unit; a fourth attempt or same-plan replacement ticket is impossible.
5. Park only after recorded escalation or takeover also fails.

`BLOCKED` requires `blocker_class:"external"` and an external-dependency or capability-gap cause. Internal decomposition and repair are not user blockers.

## Program completion

Ticket passes are not whole-program acceptance. After all registered item IDs are completed, no writer or reported verifier work remains, and a zero-remaining exact progress report is recorded, run a fresh assembled-candidate verifier. Then record:

    {"schema_version":1,"event":"program_completed","verifier_id":"final-independent-verifier","verifier_evidence_sha256":"<64-hex>","verdict":"PASS","verification_scope":"assembled","lead_reviewed":true,"processes_closed":true,"original_criteria_reconciled":true,"criteria_reconciliation_path":"<artifact>","criteria_reconciliation_sha256":"<64-hex>","candidate_fingerprint":"<64-hex>","verification_minutes":8,"verification_noncached_input_tokens":5000}

The final verifier must use an identity and evidence digest not used by any builder route, builder receipt, or slice verifier. `program_completed` is terminal. Without this fresh assembled event, even 45 completed slices remain an incomplete program.
