# Changelog

All notable changes to Sol Foreman are documented here.

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
