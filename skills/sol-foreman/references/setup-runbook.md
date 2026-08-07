# Setup runbook (agent-executable and evidence-verified)

Run this before a program that will dispatch CLI workers. It is idempotent:
every created path is verified, an existing ledger or event file is preserved,
and a failed gate stops the affected run rather than continuing with a guess.
Do not put secrets, raw authentication responses, or provider configuration in
the ledger or scratch artifacts.

Resolve `<skill-root>` as the directory containing the loaded `SKILL.md` and
run every command with standard input closed (`< /dev/null`). Use `py` instead
of `python3` where that is the available Windows launcher.

## 1. Capability probe (free)

Run the bundled sanitized probe from an unrelated working directory and retain
only its JSON output as setup evidence:

```sh
python3 "<skill-root>/scripts/probe_capabilities.py" --json < /dev/null
```

Evidence: the JSON records installed/version/auth-presence facts without a
model call. If the script exits nonzero or its JSON cannot be retained outside
the worker tree, stop: the available lanes are not evidenced.

## 2. Consent gate (before any echo)

The probe is free. Every `codex exec` or `claude -p` echo below is billable or
uses subscription quota. Before the first one, record the operator's current
session consent, provider, model/alias, intended number of calls, and billing
uncertainty in the ledger. An explicit request for Sol Foreman, Codex agents,
or Claude agents is ordinary-dispatch consent; Fable 5 still needs its
separate permission gate. If consent is absent, stop here with `NEEDS
OPERATOR`—do not turn an availability check into unapproved spend.

## 3. Claude CLI availability (free)

Only if the program plans a Claude CLI lane, run:

```sh
command -v claude
claude --version < /dev/null
```

Evidence: preserve the binary path and version in the setup scratch directory.
If either command fails, mark the Claude CLI lane `unavailable`, do not
substitute another provider, and stop any ticket that required it.

## 4. Verify each pinned tier (consent required)

Verify only models that the actual program will pin. Run one tiny echo for each
model/lane pair and preserve its stdout, stderr, exit code, and first output
line under the setup scratch directory.

```sh
# Pinned Codex model
codex exec -m <verified-model> "Reply with exactly: ok" < /dev/null

# Pinned Claude CLI model or alias
claude -p --model <verified-model-or-alias> "Reply with exactly: ok" < /dev/null
```

An exit of 0 with the expected `ok` records `tier <provider>/<model>:
verified`. Any other exit, output, entitlement error, or missing artifact
records `tier <provider>/<model>: unavailable — <evidence-path>` and stops that
lane. Never retry an unavailable ID unchanged, silently fall back, or claim a
successful echo proves the model that ultimately serves later work; the result
is availability evidence plus `requested-pin`, not `runtime-metadata-confirmed`.

## 5. Bootstrap ledger and scratch (authorized repository-write programs)

For a new program in an authorized repository, create only the required
directories and refuse to overwrite state. For read-only work, use an approved
temporary directory instead and keep equivalent state in the thread.

```sh
mkdir -p .foreman/scratch
test -d .foreman/scratch

if [ -e .foreman/ledger.md ]; then
  test -f .foreman/ledger.md && grep -Fqx '# Foreman Ledger' .foreman/ledger.md || exit 1
else
  printf '%s\n' '# Foreman Ledger' '' '## Setup Evidence' > .foreman/ledger.md
  test -s .foreman/ledger.md
fi

if [ -e .foreman/events.jsonl ]; then
  test -f .foreman/events.jsonl || exit 1
else
  : > .foreman/events.jsonl
  test -f .foreman/events.jsonl
fi
```

Evidence: `test` succeeds for all three paths, the ledger has its required
heading, and any pre-existing content remains unchanged. Record the capability
probe, consent, tier results, baseline commit/status, and scratch path in the
ledger before dispatch. For a long program, record `program_started` through
`program_guard.py record` before the first `program_guard.py dispatch`; an
empty events file is bootstrap only, not permission to dispatch.

## 6. Stop rule and handoff

Do not proceed past a failed probe, missing CLI/version, absent consent,
unverified requested tier, unsafe state path, or failed evidence write. Record
the exact command, exit code, sanitized artifact path, and input needed to
unblock in `NEEDS OPERATOR`. A green setup proves the environment and requested
route are available; it does not waive ticket preflight, provenance labeling,
process closure, or independent verification.
