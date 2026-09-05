# Sol Foreman

[![CI](https://github.com/olsenbrands/sol-foreman/actions/workflows/ci.yml/badge.svg)](https://github.com/olsenbrands/sol-foreman/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/olsenbrands/sol-foreman)](https://github.com/olsenbrands/sol-foreman/releases/latest)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

I built Sol Foreman as a standalone Codex skill for leading delegated builds
with economical routing and accountable acceptance. I designed it so the lead
remains responsible for understanding the outcome, setting observable criteria,
choosing a bounded route, reviewing returned work, and accepting only what the
evidence supports.

I optimize for cost per accepted user outcome. Lead reasoning, worker time, tool
use, repair, integration, review, and elapsed time all count. Cheap tokens,
busy tickets, and model consensus are not delivery.

## What I changed in v0.4.0

- I made the Sol workflow standalone for direct work, delegated changes, and
  longer sprints without requiring another foreman skill.
- I kept Codex as the complete baseline, with Claude and Grok as optional
  routes only when available and authorized.
- I added provider preferences among qualified routes while retaining an
  independent review quality floor and the lead's final acceptance.
- I tied lead work and delegated work to original outcomes, finite evidence
  checkpoints, bounded review rounds, and concrete recovery decisions.
- I preserved active legacy runs on their original version. An update never
  resets attempts, replaces active writers, or silently redirects old helpers.

## How it works

- Define the requested behavior, negative constraints, and proof before work
  begins.
- Use direct implementation when delegation would cost more than it saves.
- Delegate one coherent behavior at a time, with ownership and a finite stop
  condition.
- Use the smallest qualified crew. Codex-only is supported; optional Claude and
  Grok capacity can extend, not replace, the required quality floor.
- Keep independent review separate from builder claims. A reviewer does not
  accept the outcome and a green check is not a release claim.
- On a missed checkpoint, inspect the critical dependency and choose a repair,
  route change, consolidation, direct takeover, or real external blocker.
- Report evidence, remaining work, and the next gate separately from merge,
  deployment, and live acceptance when those stages apply.

## Requirements

- Codex with global skill support.
- Python 3.9 or newer for bundled dependency-free helper scripts.
- Optional: authorized Codex, Claude, or Grok CLI routes when the task benefits
  from them. No optional provider is required.

## Install v0.4.0

The canonical global destination is `~/.agents/skills/sol-foreman`. The
recommended installer uses the immutable `v0.4.0` tag and refuses to overwrite
that destination. First reconcile active work and local modifications under the
[version-change guide](skills/sol-foreman/references/compatibility.md). A disk
update does not replace instructions already loaded by an active session; start
a fresh session after a successful transition.

Ask Codex:

    Use $skill-installer to install https://github.com/olsenbrands/sol-foreman/tree/v0.4.0/skills/sol-foreman globally.

Or use Codex's built-in installer on macOS or Linux:

    python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
      --repo olsenbrands/sol-foreman \
      --path skills/sol-foreman \
      --ref v0.4.0 \
      --dest "$HOME/.agents/skills"

On Windows:

    py "%USERPROFILE%\.codex\skills\.system\skill-installer\scripts\install-skill-from-github.py" --repo olsenbrands/sol-foreman --path skills/sol-foreman --ref v0.4.0 --dest "%USERPROFILE%\.agents\skills"

The release asset `sol-foreman-v0.4.0.zip` has the installable skill at
`sol-foreman/SKILL.md`. Use it to inspect or stage the tagged source before an
upgrade; Codex's GitHub installer above is the supported installation path. Do
not copy the archive over an active skill or a symlinked development checkout.
For a prior `.codex` installation, preserve it at a versioned archive path
outside skill discovery before an operator-approved transition. Do not claim a
hot replacement of an already loaded session.

## Use

For a bounded task:

    Use $sol-foreman to define observable acceptance criteria, choose the smallest qualified route, and independently verify the result.

For a larger program:

    Use $sol-foreman to understand the original outcomes, select a bounded pilot, route and review work economically, recover missed checkpoints, and report evidence-backed progress through completion.

## Safety boundaries

- No deployment, publication, destructive data action, external message, or
  paid service is authorized merely by invoking this skill.
- Provider availability, a requested model, and a served model are distinct
  facts. Missing route evidence is disclosed rather than invented.
- Optional-provider limits trigger an announced eligible fallback, not a reset
  of the contract, evidence, or review requirement.
- Existing repository controls, user restrictions, and active-run ownership
  remain binding.
- Bundled helpers support bounded review accounting, capability discovery,
  isolated review candidates, path policy, fingerprints, and CLI lifecycle
  evidence. They do not replace the lead's judgment or project safeguards.

## Validate a source checkout

    python3 -m unittest discover -s tests -v
    python3 -m compileall -q skills tests
    python3 skills/sol-foreman/scripts/probe_capabilities.py --json

Use `py` instead of `python3` when that is the available Windows launcher. The
capability probe makes no billable model calls. It is useful only when an
optional CLI route is under consideration.

## Project resources

- [Changelog](CHANGELOG.md)
- [Contributing](CONTRIBUTING.md)
- [Security reporting](SECURITY.md)
- [Skill entrypoint](skills/sol-foreman/SKILL.md)
- [Routing and economics](skills/sol-foreman/references/routing.md)
- [Independent verification](skills/sol-foreman/references/verification.md)
- [Existing-run compatibility](skills/sol-foreman/references/compatibility.md)

## License

MIT. See [LICENSE](LICENSE).
