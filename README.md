# Sol Foreman

Sol Foreman turns the primary Codex agent into a quality-first foreman. It studies the full job, defines verification before delegation, routes bounded work to native Codex subagents or model-pinned Codex/Claude CLI workers, and accepts work only after the lead reviews real evidence.

The rule is simple: save usage only among models that clear the quality bar. If quality is uncertain, route upward.

## What it adds

- Native Codex subagent orchestration for integrated parallel work.
- Optional model-pinned `codex exec` workers when an exact Codex seat and effort are required.
- Optional Claude CLI workers for implementation or cross-family verification.
- Verification criteria written before every assignment.
- Disjoint write sets, bounded retries, durable ledgers, blind verification, and lead-owned acceptance.
- Live capability probing so a dated model table never overrides the user's actual account.
- A hard permission gate before Claude Fable 5 and its distinct expensive quota.

## Install

Ask Codex:

    Use $skill-installer to install https://github.com/olsenbrands/sol-foreman/tree/main/skills/sol-foreman globally.

Or run the built-in installer directly on macOS/Linux:

    python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
      --repo olsenbrands/sol-foreman \
      --path skills/sol-foreman

On Windows:

    py "%USERPROFILE%\.codex\skills\.system\skill-installer\scripts\install-skill-from-github.py" --repo olsenbrands/sol-foreman --path skills/sol-foreman

Start a fresh Codex session after installation so the new skill is discoverable.

Invoke it explicitly:

    Use $sol-foreman to plan, delegate, and independently verify this multi-stage task.

## Capability lanes

| Lane | Required | Exact model pinning |
|---|---|---|
| Native Codex subagents | A Codex surface with collaboration tools | Only when the active spawn surface exposes it |
| Codex CLI workers | Installed and authenticated `codex` | Yes, through `codex exec -m` |
| Claude CLI workers | Installed and authenticated `claude` | Yes, through `claude -p --model` |
| Solo discipline | Codex only | Not applicable |

All lanes degrade honestly. Missing collaboration or CLI access does not become fake verification.

## Model currency

The bundled routing snapshot was reviewed on 2026-07-18. Sol Foreman runs a local, non-billable capability probe before routing and tells the lead to refresh official provider documentation when it detects a newer Codex generation, stale model cache, or unfamiliar model.

## Safety

- Workers never spawn workers.
- Parallel writers require provably disjoint file sets or isolation.
- External CLI agents receive narrow permissions and context.
- The lead inspects diffs, reruns gates, and owns final acceptance.
- Fable 5 requires explicit permission unless the user already requested it in the current session.
- Mythos is never used without explicit request, verified access, and authorized defensive-security scope.

## License

MIT © Jordan Olsen
