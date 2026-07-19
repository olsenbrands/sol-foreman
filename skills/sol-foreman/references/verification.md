# Verification and acceptance

Define proof before dispatch. Verification exists to test the user's goal, not to justify a worker's output.

## Contents

- [Write strong criteria](#write-strong-criteria)
- [Map proof to criteria](#map-proof-to-criteria)
- [Layer the checks](#layer-the-checks)
- [Progressive program verification](#progressive-program-verification)
- [Blind verification](#blind-verification)
- [Hardened Claude blind verifier](#hardened-claude-blind-verifier)
- [Mutation and quarantine backstop](#mutation-and-quarantine-backstop)
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

## Progressive program verification

Match verification scope to candidate maturity:

1. At the early artifact checkpoint, inspect scope, architecture direction, and the smallest deterministic reproduction.
2. At slice completion, run the slice's focused behavior and package gates and review its diff.
3. At an integration seam, assemble accepted slices and run the boundary contract once.
4. After the candidate is coherent, run full repository, customer-path, and blind-verifier gates.

Do not repeatedly run the entire expensive suite on a slice that has not cleared its focused gate. Do not defer all review until dozens of slices have accumulated. A slice pass is provisional until the assembled candidate passes its original cross-slice criteria.

## Blind verification

Use a fresh agent or ephemeral CLI process. Give it only:

- the original user request verbatim;
- the lead-authored **product** criteria it can observe;
- baseline and candidate identifiers;
- changed product paths or product-only diff;
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

Keep product verification separate from orchestration audit. A verifier that
cannot inspect `.foreman` cannot verify dispatch, ticket ownership, model
selection, process closure, builder rationale, or lead conclusions. Mark those
criteria `NOT OBSERVABLE` for that verifier and give them to a separate
auditor with an explicitly authorized audit package, or retain them for lead
review. Do not mix them into the product verdict.

## Hardened Claude blind verifier

Use this as the default when Claude verifies a candidate. Run it from a fresh
temporary run directory, never from the source repository. Before dispatch,
run `claude --help` and `claude --version`; retain the help/version evidence
with the run.

1. Create a fresh `RUN_DIR` outside the source tree. Write a JSON array of
   explicit product paths, then materialize `CANDIDATE` with
   `scripts/materialize_candidate.py`. The script rejects absolute/traversing
   paths, overlapping entries, metadata/cache paths, escaping intermediate or
   final symlinks, and special files. It never copies `.git`, `.foreman`, or
   runtime caches, including through case aliases, symlinks, Windows junctions,
   or other resolved filesystem aliases; aliases outside source are rejected. For
   identical cross-platform behavior it always dereferences a safe internal
   symlink and records that transformation. Treat the candidate as reduced
   fidelity; use another isolation method when symlink identity is a
   product criterion. If an approved gate requires Git
   metadata, initialize and commit a disposable candidate-only repository
   after materialization; never expose source `.git`.
2. Give Claude only `CANDIDATE`, a product-only ticket, the product-only diff,
   and exact non-mutating gates. Do not give it the source-repository path.
3. Write `{"mcpServers":{}}` to `RUN_DIR/empty-mcp.json`. Write all verifier
   output outside `CANDIDATE`.
4. Fingerprint both the source tree and `CANDIDATE` before dispatch with the
   bundled `scripts/fingerprint_tree.py --manifest`. It covers every product
   entry's relative path, type, mode, link target when applicable, and SHA-256
   content hash for regular files. It excludes `.git`, `.foreman`, Python
   bytecode, and common runtime caches at any depth by default but does not
   omit other ignored, hidden, or untracked product files.
5. Freeze both trees until their after-fingerprints are captured. Keep verifier
   metadata, live ledger updates, streams, reports, caches, and temporary files
   in `RUN_DIR`; copy approved evidence into the source tree only after the
   comparisons finish.
6. Substitute each `<exact-nonmutating-gate>` with a known read/test command.
   Route its caches, reports, and temporary output to `RUN_DIR`; do not allow a
   gate that writes in `CANDIDATE`.
7. Fingerprint source and candidate before the run. Invoke Claude through
   `scripts/run_cli_worker.py`. Set `--cwd <CANDIDATE>`, supply source and
   candidate as `--protected-root`, and explicitly designate only candidate as
   `--read-only-cwd-root <CANDIDATE>`. Keep the ticket, stream, stderr, and
   receipt under `RUN_DIR`. The wrapper rejects source as a working directory,
   closes the worker process tree, and records terminal closure. Use this
   worker argument vector after `--`:

    claude -p --model <verified-model-or-alias> --effort <level> --safe-mode --strict-mcp-config --mcp-config <empty-mcp.json> --no-chrome --disable-slash-commands --no-session-persistence --permission-mode dontAsk --tools Read,Grep,Glob,Bash --allowed-tools Read Grep Glob "Bash(git status --porcelain=v1 -uall)" "Bash(git diff --no-ext-diff --binary)" "Bash(rg <approved-pattern> <approved-path>)" "Bash(<exact-nonmutating-gate>)" --disallowed-tools Edit,Write --output-format stream-json --include-hook-events --verbose

8. Record the wrapper receipt and compare source/candidate fingerprints after
   the run. Preserve the raw stream separately from any human-readable report.
   Do not replace, compact, or overwrite raw evidence.

The portable wrapper avoids shell interpolation and pipelines. Create the
temporary directory through the active platform's safe temporary-directory
facility. Use `python3` on macOS/Linux and `py` when that is the available
Windows launcher. Treat every Claude flag as version-discovered rather than a
cross-version promise.

The named Claude flags above are the current template, not a compatibility promise.
If a named flag is unavailable, use `claude --help` to find an equivalent and
record the discovered flag and version. Never guess or silently omit a
protection. If no equivalent can disable ambient customization, restrict MCP
to the empty config, disable Chrome and slash commands, deny edits/writes,
prevent persistence, or preserve raw streaming evidence, return
`NEEDS_CONTEXT` instead of issuing a blind verdict.

## Mutation and quarantine backstop

For a verifier that can execute shell commands:

1. Compare both before/after fingerprints and retain the comparison result.
   Also retain the raw stream and fail the run on a reported write attempt.
2. Forbid edits, fixes, destructive git commands, deployment, production
   access, and all paths outside `CANDIDATE` and `RUN_DIR`.
3. Void the verdict on any source-tree or candidate fingerprint difference,
   any reported write attempt, or an incomplete fingerprint. Do not retry the
   verifier against the same surface.
4. Preserve `RUN_DIR`, the raw stream, both fingerprints, and exit status for
   diagnosis. If `CANDIDATE` changed, quarantine that isolated copy under
   `RUN_DIR/quarantine/` with its evidence.
5. Never automatically delete, clean, reset, or quarantine an artifact in the
   user's source tree. Preserve unknown source-tree artifacts for diagnosis and
   ask the owner to decide their disposition.

Tool restrictions plus this check are defense in depth, not a perfect sandbox. Bash can write.

## Parent review

The lead must independently:

1. Read the actual changed files or diff.
2. Re-run the most important gates where practical.
3. Audit the complete raw event stream, including denied tool requests and
   discrepancies omitted from the report, then reconcile worker and verifier
   evidence.
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
