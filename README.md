# Sol Foreman

[![CI](https://github.com/olsenbrands/sol-foreman/actions/workflows/ci.yml/badge.svg)](https://github.com/olsenbrands/sol-foreman/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/olsenbrands/sol-foreman)](https://github.com/olsenbrands/sol-foreman/releases/latest)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Sol Foreman is a quality-first Codex skill for delegating work to native Codex subagents, model-pinned Codex CLI workers, and Claude CLI agents. The primary agent defines observable completion criteria before dispatch, selects the strongest suitable worker, monitors progress, independently verifies returned work, and remains accountable for final acceptance.

The rule is simple: save usage only among models that clear the quality bar. If quality is uncertain, route upward.

## What's new in v0.3.0

This release makes the worker route easier to trust and the CLI lane easier to
operate safely:

- **Honest routing evidence.** A requested model, a worker's identity answer,
  inherited native context, and provider runtime metadata remain distinct. The
  routing guide now explains silent substitution risks and records current
  Claude CLI behavior without pretending a request proves the served model.
- **Visible Claude CLI transport where supported.** A long Claude CLI job can
  ride inside one narrow native-Codex wrapper so the harness shows a live work
  item and delivers completion to the lead. The wrapper is visible; the inner
  Claude process is not, and direct launch remains the right fallback for
  short calls or harnesses without native activity.
- **Safer durable worker evidence.** The launcher refuses symlink/non-regular
  artifact entries and existing receipts, closes a child if initial receipt
  tracking fails, and redacts gateway URLs from durable receipt and stream
  artifacts.
- **Executable release discipline.** New setup and cross-family release
  runbooks make consent, availability, evidence, review, and release hygiene
  explicit gates instead of conventions.

## Why use it

- Define verification criteria before every assignment.
- Route work by capability, risk, context, and required independence.
- Keep parallel writers isolated or prove their write sets are disjoint.
- Start long programs with a small independently verified pilot.
- Count completed original program items instead of worker activity or slices.
- Stop repeated same-cause failures, retry loops, and verification backlogs.
- Require fresh assembled-candidate verification before declaring a program complete.
- Keep the lead responsible for diff review, reproduced evidence, and final acceptance.

## Operating modes

| Mode | Use it for | Control level |
|---|---|---|
| Lightweight | One bounded, low-risk worker with no shared-write ambiguity | Inline criteria, one write set, lead verification, no program ledger |
| Program | Multiple tickets or workers, long-running work, parallel writes, or material risk seams | Preflight tickets, append-only state, pilots, breakers, exact progress, independent verification |

## Worker lanes

| Lane | Requirement | Exact model pinning |
|---|---|---|
| Native Codex subagents | A Codex surface with collaboration tools | Only when the active spawn surface exposes it |
| Codex CLI workers | Installed and authenticated `codex` | Yes, through `codex exec -m` |
| Claude CLI workers | Installed and authenticated `claude` | Yes, through `claude -p --model` |
| Solo discipline | Codex only | Not applicable |

Missing collaboration or CLI access degrades honestly. It never becomes fake delegation or fake verification.

## Requirements

- Codex with global skill support.
- Python 3.9 or newer for the dependency-free helper scripts.
- Optional: Codex CLI or Claude Code CLI for model-pinned external workers.
- Windows, macOS, or Linux.

## Install

Ask Codex:

    Use $skill-installer to install https://github.com/olsenbrands/sol-foreman/tree/v0.3.0/skills/sol-foreman globally.

Or use Codex's built-in installer on macOS or Linux:

    python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
      --repo olsenbrands/sol-foreman \
      --path skills/sol-foreman \
      --ref v0.3.0

On Windows:

    py "%USERPROFILE%\.codex\skills\.system\skill-installer\scripts\install-skill-from-github.py" --repo olsenbrands/sol-foreman --path skills/sol-foreman --ref v0.3.0

Start a fresh Codex session after installation so the skill catalog refreshes.

## Use

For a bounded task:

    Use $sol-foreman to delegate this task to one suitable worker, define the verification criteria first, and independently verify the result.

For a larger program:

    Use $sol-foreman to understand this repository and tracker, define what done means, select a bounded pilot, route the right agents, monitor and verify their work, and continue only while accepted throughput supports the plan.

Sol Foreman asks separately before using Claude Fable 5 unless the user already requested it in the current session.

## Program safeguards

- Original program item IDs are registered before dispatch.
- Active and reported-but-unverified work both consume capacity and retain ownership.
- Portable path identities reject repository-root, metadata, cache, symlink, junction, and external-path escapes.
- Attempt three requires a materially different capability route or lead takeover.
- Repeated same-cause failures require an exact report and substantive replan.
- Any terminal parked unit halts replacement until report and replan.
- Builders cannot certify their own work.
- Final assembled verification cannot reuse builder or slice-verifier evidence.
- Worker subprocesses must produce terminal receipts with confirmed process-tree closure.

## Model currency

The bundled routing snapshot was reviewed on 2026-07-19. Sol Foreman runs a local, non-billable capability probe before selecting pinned CLI workers and requests a documentation refresh when it detects a newer generation, stale cache, or unfamiliar model.

## Privacy and safety

- Tickets and evidence must not contain secrets, credential values, raw authentication responses, or unnecessary personal data.
- The capability probe exposes only sanitized availability and authentication-presence fields.
- External workers receive narrow context, permissions, and write authority.
- Blind verifiers receive a product-only candidate without builder narratives or Foreman metadata.
- Fable 5 requires explicit permission unless already requested.
- Mythos is never selected without explicit request, verified access, and authorized defensive-security scope.

## Validate a source checkout

Run the dependency-free suite:

    python3 -m unittest discover -s tests -v
    python3 -m compileall -q skills tests
    python3 skills/sol-foreman/scripts/probe_capabilities.py --json

Use `py` instead of `python3` when that is the available Windows launcher. The capability probe makes no billable model calls.

The suite includes ticket preflight, exact program state, full 45-item completion, retry and breaker behavior, candidate isolation, cross-platform path policy, process closure, privacy-safe capability probing, and deterministic fingerprints.

## Known limits

- Native subagent model identity is only as precise as the active collaboration surface exposes.
- Current Codex CLI JSONL does not expose a served-model field, so a Codex
  `-m` request remains `requested-pin` until a future provider metadata source
  can prove otherwise.
- A native wrapper is a harness-visible transport item, not proof that the
  inner Claude subprocess is visible or that its requested model served.
- Subscription and model entitlement must be confirmed locally; bundled model guidance is not an entitlement claim.
- Sol Foreman improves control and verification but cannot guarantee that every delegated task succeeds.

## Project resources

- Changes: [CHANGELOG.md](CHANGELOG.md)
- Contributing: [CONTRIBUTING.md](CONTRIBUTING.md)
- Security reporting: [SECURITY.md](SECURITY.md)
- Skill entrypoint: [skills/sol-foreman/SKILL.md](skills/sol-foreman/SKILL.md)
- Setup runbook: [setup-runbook.md](skills/sol-foreman/references/setup-runbook.md)
- Release review process: [release-process.md](skills/sol-foreman/references/release-process.md)

## Maintainer

Created and maintained by [Jordan Olsen](https://dontsleeponai.com/).

## License

MIT. See [LICENSE](LICENSE).
