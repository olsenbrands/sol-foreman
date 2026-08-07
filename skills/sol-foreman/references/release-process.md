# Cross-family adversarial release process

Use this process for a meaningful Sol Foreman release. The builder and final
reviewer must be from different model families: this skill's Codex-side change
is reviewed by a frontier-class Claude in a fresh context. A green local suite
is necessary evidence, not release approval.

## 1. Prepare a read-only review ticket

Write a ticket outside the candidate tree with the original release goal,
repository path, base commit, current diff, exact verification commands,
scope exclusions, and known limitations. The reviewer receives the original
criteria, not the builder's conclusion. Require a read-only session with no
edit tools and no production credentials.

Start the reviewer from a dedicated temporary directory, not the candidate
tree, and grant only the named candidate/ticket paths. Capture `git status
--short` before and after the review. A provider CLI may create local cache or
vector-store files despite a read-only task; such a write is review-hygiene
failure to remove or move outside the candidate and report before the verdict
can be accepted.

The report contract is strict:

1. Its first line is exactly `VERDICT:APPROVED` or `VERDICT:REVISE`.
2. `VERDICT:REVISE` is followed by severity-ranked findings, each with an
   exact file:line, concrete impact, and a reproducible reason.
3. `VERDICT:APPROVED` may include residual notes, but it must state why no
   release-blocking finding remains.

Malformed output, a missing transcript, or a reviewer that mutates the
candidate is a failed review, never implicit approval.

## 2. Run bounded review rounds

Run at most three fresh Claude review rounds. Preserve each raw transcript,
command, exit code, ticket path, and candidate commit/diff identity.

For a `REVISE` verdict, the lead first verifies each claimed finding against
the candidate. The lead may reject a claim only with concrete counter-evidence
(for example, a test, source path, or platform condition outside the reviewer's
visible context). Batch every accepted finding from one round into **one** fix
wave. Each code fix receives a deterministic focused test, then the full suite
runs before the next fresh review. Do not create one worker or one commit per
finding.

Stop and report rather than looping when either condition holds:

- three review rounds have not produced `VERDICT:APPROVED`; or
- two consecutive fix waves fail to resolve the same canonical finding set.

## 3. Release gate

Only after an `APPROVED` transcript, rerun the full suite from the exact
candidate and inspect release hygiene: working-tree scope, leftover temporary
labels or artifacts, manifest/version/README/CHANGELOG consistency, generated
or tracked cruft, and the release notes' honest limitations. Reconcile the
reviewed diff with the tagged commit. Any discrepancy reopens review.

Tagging and publication are last. Never push `main`, create a tag, or publish
a release before the approved transcript and release-gate evidence exist.
