# Changelog

All notable changes to Sol Foreman are documented here.

## 0.4.0 - 2026-09-05

The standalone Sol lead release. It replaces the legacy program-control package
for new work with an outcome-focused workflow that keeps delivery, economics,
and independent acceptance connected.

### Added

- A standalone Sol workflow for direct work, delegated changes, sprints,
  recovery, and safe continuation across sessions.
- Review reservation accounting through `review_guard.py`, including immutable
  original outcome IDs, active-reservation protection, phase-specific rounds,
  migration, and bounded higher-round decisions.
- Routing guidance for Codex-only crews with optional Claude and Grok routes,
  user preferences among qualified providers, and a non-negotiable review floor.
- Explicit first-artifact, review, and original-outcome checkpoints that require
  a lead decision rather than unlimited tracker activity.
- A compatibility boundary for preserving old installations, active writers,
  local patches, and legacy helper behavior during upgrades.

### Changed

- The public documentation now describes Sol in first person as a standalone
  lead and gives tagged `v0.4.0` installation guidance plus the versioned source
  archive layout.
- Conditional tools retain the proven capability probe, CLI lifecycle wrapper,
  candidate materialization, path policy, and tree fingerprint helpers.

### Removed

- The legacy JSON ticket preflight and program guard are not bundled for new
  runs. Their history remains available through Git, and existing legacy runs
  must remain on their recorded version until reconciled.

### Important limits

- The review guard bounds review reservations only. It does not enforce every
  write set, observe all worker launches, or accept product outcomes.
- Provider examples and routing guidance are starting hypotheses, not a claim
  of universal provider reliability or entitlement.

## 0.3.0 - 2026-08-07

The "trust the route, see the work" release. It brings the genuine, applicable
lessons from the fable-foreman v0.3.0 and claudemix routing study to the
Codex-side skill, while retaining the provenance, JSONL dispatch log, and
program-control systems Sol Foreman already had.

### Added

- A four-label silent-fallback and self-report guide with current Claude Code
  and Claude CLI empirical results, plus countermeasures tied to Sol Foreman's
  existing provenance system.
- Conditional native-Codex transport for longer Claude CLI work: visible
  wrapper activity and completion notification where the harness supports it,
  with an explicit failure map and no claim that the inner process is native or
  served by the requested model.
- An agent-executable setup runbook covering the non-billable capability probe,
  spend consent, per-lane availability evidence, Claude version checks, and
  no-clobber ledger/scratch bootstrap.
- A cross-family release-review process: fresh frontier Claude review,
  verdict-first reporting, one deterministic fix wave per round, bounded stop
  rules, and a final hygiene gate before tagging.

### Changed

- CLI receipts now create exclusively before the child continues, distinguish
  existing evidence from an I/O failure, and conservatively redact every
  `http(s)` URL from derived receipt command/error metadata while retaining raw
  worker stream artifacts byte-for-byte.
- Artifact entries reject direct symlinks and non-regular files; denial of a
  POSIX process-group signal falls back to the known direct child and reports
  incomplete descendant closure honestly when needed.
- The public regression suite now includes deterministic launcher tests for
  these evidence, redaction, and process-closure cases.

### Known limitations

- Current Codex CLI JSONL has no served-model field. A requested `-m` model is
  not treated as runtime confirmation.
- The wrapper makes the native transport wrapper visible only where the active
  harness supports it; the Claude subprocess itself remains indirect.
- Model availability echoes establish availability for a requested route, not
  the model that will serve every later turn.

## 0.2.0 - 2026-07-19

### Added

- Lightweight mode for one bounded worker without unnecessary program-state ceremony.
- Guarded program mode with an explicit registry of original item IDs.
- Pilot-before-fan-out enforcement for long programs.
- Exact accepted-throughput, cost, and projection reporting.
- Capacity limits that include reported-but-unverified work.
- Cross-platform canonical path identity and candidate-materialization policy.
- Fresh assembled-candidate acceptance after all program items complete.
- POSIX detached-descendant tracking and suspended Windows Job Object assignment.
- A 65-test dependency-free suite, including a complete 45-item program trace.

### Changed

- Dispatch now requires deterministic ticket preflight and evidence-bound route metadata.
- Verification, original-item completion, and whole-program acceptance are separate states.
- Attempt-three escalation must change worker identity, capability route, and route evidence.
- Install examples use the immutable `v0.2.0` release tag.

### Fixed

- Prevented builder receipt evidence from being reused as final verifier evidence.
- Prevented terminal parked units from creating retry or replacement dead ends.
- Prevented simultaneous breaker, attempt-exhaustion, and pilot-exhaustion reasons from being cleared by an incomplete report.
- Prevented reported-but-unverified work from losing ownership or bypassing concurrency limits.
- Prevented case, symlink, junction, metadata, cache, and external path aliases from bypassing write isolation.
- Prevented false process-tree closure when descendants detach or observation is unavailable.
- Made malformed model-generation parsing deterministic across supported Python versions.
- Fixed Windows worker startup by using the documented Win32 suspended-creation flag.

## 0.1.1 - 2026-07-18

- Hardened worker contracts, model evidence labels, candidate fingerprinting, and privacy-safe capability probing.

## 0.1.0 - 2026-07-18

- Initial public release.
