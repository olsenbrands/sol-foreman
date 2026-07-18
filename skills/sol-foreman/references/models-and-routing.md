# Models and routing

This snapshot was reviewed on **2026-07-18**. Treat it as a starting point, not entitlement proof.

## Refresh before routing

1. Run `scripts/probe_capabilities.py --json`.
2. Prefer the account's current Codex model cache and CLI help over this snapshot for availability.
3. If the cache is missing, stale, or contains unfamiliar models, check current official provider documentation.
4. Verify any exact model/effort pair with a tiny non-destructive call before a long dispatch, after the user has consented to billable work.
5. Record verified and unavailable pairs in the ledger.
6. If a newer tier clearly supersedes this map, route by its published capability and update this reference when the installed skill source is user-owned and writable. Re-run skill validation after editing.

Do not infer access from a launch article. Rollouts, plan tiers, regions, authentication modes, and CLI versions can differ.

## Codex snapshot

OpenAI's GPT-5.6 launch defines durable capability tiers:

| Seat | Current Codex slug on this machine | Dated API price / MTok in-out | Positioning | Route here |
|---|---|---:|---|---|
| Sol | `gpt-5.6-sol` | $5 / $30 | Flagship frontier agentic coding model | Ambiguous, multi-stage, security-sensitive, integration-heavy, or final judgment |
| Terra | `gpt-5.6-terra` | $2.50 / $15 | Balanced everyday agentic coding model | Well-specified substantive implementation, tests, refactors, research, and review |
| Luna | `gpt-5.6-luna` | $1 / $6 | Fast and affordable agentic coding model | Clear repeatable tasks, reconnaissance, extraction, and mechanical edits |

Quality-first defaults:

- Use **Sol xhigh or max** for hard architecture, novel debugging, concurrency, security judgment, or final acceptance. Use `ultra` only when automatic multi-agent fan-out is valuable and the account supports it.
- Use **Terra high or xhigh** for serious implementation. Terra is the default workhorse; choose it over Luna whenever judgment or cross-file integration matters.
- Use **Luna medium or high** for narrow work with crisp tests. Escalate immediately when the task becomes ambiguous.
- Keep GPT-5.5, GPT-5.4, GPT-5.4 Mini, and Codex Spark as compatibility or special-latency fallbacks when GPT-5.6 seats are unavailable; do not prefer an older or weaker seat merely because its name is familiar.

The native subagent surface may not expose a model argument. In that case, do not pretend it does. Use the native child with inherited/unknown seat, or use `codex exec -m <slug>` when exact pinning is required.

Official source: https://openai.com/index/gpt-5-6/

## Claude snapshot

| Seat | Claude CLI model | Dated API price / MTok in-out | Positioning | Route here |
|---|---|---:|---|---|
| Fable 5 | `fable` or `claude-fable-5` | $10 / $50 | Anthropic's most capable widely released model for long-horizon agents | Exceptional frontier need only, behind the explicit Fable permission gate |
| Opus 4.8 | `opus` or `claude-opus-4-8` | $5 / $25 | Complex agentic coding and enterprise work | Frontier cross-family build or verification when Fable is not justified |
| Sonnet 5 | `sonnet` or `claude-sonnet-5` | $3 / $15 | Best combination of speed and intelligence | Default Claude workhorse |
| Haiku 4.5 | `haiku` or `claude-haiku-4-5` | $1 / $5 | Fastest, near-frontier model | Scanning, extraction, mechanical work |
| Mythos 5 | `claude-mythos-5` | $10 / $50 | Limited defensive-cyber release with Fable-class capability | Never route without explicit request, verified access, and authorized defensive scope |

Prices above are the official API list-price snapshot on the review date. Sonnet 5 had temporary introductory pricing through 2026-08-31. Subscription credits and usage limits do not map directly to API token prices; probe the user's billing mode and never promise savings from this table alone.

Claude routing defaults:

- Use **Opus 4.8 xhigh** for demanding coding, autonomous debugging, and skeptical verification.
- Use **Sonnet 5 high or xhigh** for substantive implementation and ordinary cross-family review.
- Use **Haiku 4.5** for bounded FAST work. Upgrade when it must reason across interacting systems.
- Use **Fable 5** only after permission. State why Opus/Sonnet or GPT-5.6 Sol is insufficient for this particular task.
- Treat Claude model IDs from 4.6 onward as pinned releases, not evergreen aliases. Refresh the reference when a newer release appears.

Official sources:

- https://platform.claude.com/docs/en/about-claude/models/overview
- https://platform.claude.com/docs/en/about-claude/models/model-ids-and-versions
- https://platform.claude.com/docs/en/about-claude/models/choosing-a-model
- https://platform.claude.com/docs/en/about-claude/models/introducing-claude-fable-5-and-claude-mythos-5
- https://platform.claude.com/docs/en/about-claude/models/whats-new-claude-4-8
- https://platform.claude.com/docs/en/about-claude/models/whats-new-sonnet-5

## Choose effort

Use effort for reasoning difficulty:

- `low` or `minimal`: deterministic scans, formatting, extraction.
- `medium`: ordinary bounded execution.
- `high`: cross-file logic, testing, review, edge cases.
- `xhigh`: hard debugging, architecture, security, autonomous long-horizon work.
- `max`: the hardest frontier reasoning where extra time and usage are justified.
- `ultra`: supported Codex seats only; automatic parallel-agent coordination, announced before use.

Do not route by line count. A ten-line authorization fix can be FRONTIER; a thousand-line generated rename can be FAST.

## Break provider ties

When multiple seats clear the bar:

1. Prefer the stronger expected result.
2. Prefer cross-family independence for build versus verification.
3. Prefer the user's explicit provider or account preference.
4. Prefer the seat under less quota pressure.
5. Prefer the cheaper seat only after the first four conditions preserve the quality bar.
