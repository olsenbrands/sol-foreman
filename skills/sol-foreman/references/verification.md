# Verification and acceptance

Define proof before dispatch. Verification exists to test the user's goal, not to justify a worker's output.

## Contents

- [Write strong criteria](#write-strong-criteria)
- [Map proof to criteria](#map-proof-to-criteria)
- [Layer the checks](#layer-the-checks)
- [Blind verification](#blind-verification)
- [Mutation backstop](#mutation-backstop)
- [Parent review](#parent-review)
- [Disagreement](#disagreement)
- [Fix loop](#fix-loop)
- [Acceptance labels](#acceptance-labels)

## Write strong criteria

Make each criterion:

- **Relevant:** directly supports the requested outcome.
- **Observable:** produces a state, behavior, or artifact a reviewer can inspect.
- **Independent:** can pass or fail without vague holistic judgment.
- **Achievable:** fits the worker's tools, permissions, environment, and time.
- **Scoped:** does not smuggle unrelated improvements into the task.
- **Evidence-bound:** names the proof required.

Weak: `The implementation is robust.`

Strong:

- `VC-1: A duplicate request with the same idempotency key creates one payment row; prove with focused test <path/test-name>.`
- `VC-2: The production build command from CI exits 0.`
- `VC-3: No file outside <write set> changes; prove with git diff --name-only <baseline>.`

When visual or interactive behavior matters, require a rendered or end-to-end check. Type checks are not substitutes for customer-path proof.

## Map proof to criteria

Use a table during final review:

| Criterion | Required proof | Worker evidence | Lead reproduction | Disposition |
|---|---|---|---|---|
| VC-1 | focused behavior test | artifact/path | command + result | PASS/FAIL |

Missing proof is not a pass.

## Layer the checks

Run from cheapest and most deterministic to most judgment-heavy:

1. Scope and repository-state check.
2. Formatting, static analysis, type check, and focused tests.
3. The project's actual build or CI gate.
4. Behavioral, visual, integration, or customer-path proof.
5. Diff review against architecture, security, and regression risks.
6. Blind independent verification.

A deterministic failure outranks a model verdict.

## Blind verification

Use a fresh agent or ephemeral CLI process. Give it only:

- the original user request verbatim;
- the lead-authored criteria;
- baseline and candidate identifiers;
- changed paths or diff;
- exact gates it must reproduce;
- read-only constraints;
- verdict format.

Do not include:

- builder reasoning;
- builder summaries;
- claimed results;
- the lead's preferred conclusion;
- suspected bugs unless the task is explicitly to reproduce them.

Ask the verifier to derive its own understanding of correctness before reading the change.

Cross-family verification is preferred when it adds real independence. Use Claude to verify Codex work or a fresh Codex seat to verify Claude work. Do not spend cross-family usage on pure formatting or documentation unless risk warrants it.

## Mutation backstop

For a verifier that can execute shell commands:

1. Start from a committed candidate or isolated copy.
2. Record `git rev-parse HEAD` and `git status --porcelain`.
3. Forbid edits, fixes, destructive git commands, deployment, and production access.
4. Re-check HEAD and status after the verdict.
5. Void the verdict if the verifier mutated the candidate.

Tool restrictions plus this check are defense in depth, not a perfect sandbox. Bash can write.

## Parent review

The lead must independently:

1. Read the actual changed files or diff.
2. Re-run the most important gates where practical.
3. Reconcile worker and verifier evidence.
4. Check every original requirement, including negative constraints.
5. Confirm the verification criteria themselves remain reasonable.
6. Decide acceptance.

Do not outsource final judgment to the verifier.

## Disagreement

- If either reviewer reproduces a deterministic failure, treat the criterion as failed until explained.
- For suspected flakiness, run at most three total characterization attempts. Inconsistent results remain a failure and the flake is a finding.
- If a verifier identifies an out-of-scope observation, record it separately. Do not convert it into a hidden acceptance requirement.
- If the worker and verifier disagree without reproducible proof, mark the criterion BLOCKED, not passed.

## Fix loop

When a criterion fails:

1. Verify that the criterion tests the real goal and was stated correctly.
2. Preserve the failure evidence.
3. Give one fix worker the complete findings list and relevant evidence.
4. Require the same full verification contract after the fix.
5. Use a fresh verifier.

Do not narrow the criteria after seeing a failure merely to make the work pass. Correct criteria only when they were genuinely irrelevant, impossible, ambiguous, or based on a false assumption; record why.

## Acceptance labels

Use:

- **VERIFIED:** all required criteria have lead-reviewed evidence and required independent verification passed.
- **SELF-REVIEWED:** criteria passed only through the lead's own review; disclose reduced assurance.
- **NEEDS FIX:** one or more criteria failed and an in-scope correction path remains.
- **BLOCKED:** completion requires user input, credentials, external state, unavailable capability, or an unresolved proof conflict.

Never label partial evidence as verified.
