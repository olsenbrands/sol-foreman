# Models, evidence, and routing

This snapshot was reviewed on **2026-07-18**. It describes provider positioning and a local Codex cache observation, not account entitlement, current quota, billing permission, or runtime use.

## Resolve the skill and refresh the crew

Resolve this file and `scripts/probe_capabilities.py` from the directory containing the loaded `SKILL.md`; never assume the target repository contains the skill. Then:

1. Run the skill-relative sanitized capability probe.
2. Prefer its fresh exact Codex cache entry and CLI help over this dated table for local availability.
3. Use supplied official/current evidence for unfamiliar, missing, or stale entries. Return `NEEDS_CONTEXT` if a material routing fact remains unsupported.
4. Record availability evidence and its uncertainty in the ledger; do not convert it into an entitlement claim.
5. For a short job, accept a fresh exact cache entry plus CLI acceptance of the requested flags without a billable entitlement probe. Record `live-entitlement-probe: not-run` and the remaining uncertainty.
6. For a long, costly, or high-risk job, obtain consent before a tiny non-destructive confirmation. Record its raw approved metadata and result.

CLI acceptance shows that the invocation was accepted; it does not by itself confirm the model that completed the work.

## Evidence labels

Use these exact labels. Preserve all applicable labels rather than replacing weaker evidence with a stronger-looking summary.

| Label | Meaning | Does not prove |
|---|---|---|
| `requested-pin` | The lead requested a model and effort through a supported invocation or configuration. | Availability, acceptance, or runtime use. |
| `worker-self-report` | The worker claimed its model or effort in its own report. Preserve the claim and source. | Independent model identity. |
| `native-inherited-unconfirmed` | A native child may inherit the parent/runtime seat, but no supported pin plus runtime identity was observed for that child. | The inherited model, effort, or exact seat. |
| `runtime-metadata-confirmed` | Approved provider or CLI runtime metadata identifies the actual model; include effort when metadata exposes it. | That the model's output met criteria. |

Record the requested model/effort separately from each label, source path or event ID, timestamp, and any disagreement. Use `runtime-metadata-confirmed` only for the fields actually present. An accepted request plus self-report remains `requested-pin` + `worker-self-report`, not confirmation.

## Identity self-report nuance (2026-08-07)

`worker-self-report` is a preserved claim, not proof of a model's weights or
serving route. Identity answers track the prompt and system context a worker
received; a harness that injects the worker's identity makes the answer
usually right, but still does not turn it into independent runtime evidence.
The current Claude Code checks resisted identity priming in three of three
attempts, including a false splitter-style system note. That is reassuring
about this harness's current anchoring, not a provenance mechanism. Identity
questions are noise with the shape of a check; resolve any material dispute
with approved runtime metadata instead.

## Empirical Claude CLI status (2026-08-07)

Three non-interactive `claude -p --model <id> "Reply with exactly: ok"`
probes ran on this machine. The current `haiku` alias returned `ok` with exit
code 0. A nonexistent ID (`claude-nonexistent-99`) and a plausible but wrong
dated ID (`claude-haiku-4-5-20251002`) each exited 1 and reported that the
selected model might not exist or be inaccessible. Neither invalid request
silently produced `ok` or another successful response.

That is current-build evidence of loud failure for these two invalid-ID cases,
not a warranty that every provider, account policy, gateway, deprecated alias,
or future Claude Code build will reject instead of substitute. A claude-cli
`requested-pin` therefore remains request-side evidence: preserve the command,
exit status, and raw stream, and upgrade it only if provider runtime metadata
identifies the model that actually served the turn.

## Silent-fallback hazard

A runtime can accept a model-routing request yet serve a different seat without
an actionable error. This is a routing failure, not evidence that the work is
bad or that a worker lied; organization policy, stale aliases, unsupported
tiers, and gateways can all create it. The documented claudemix field case
(2026-08) demonstrated the class: a foreign model requested through one Claude
Code configuration surface was ignored and a Claude model served, while a
different supported configuration surface routed through the proxy. Treat that
as a caution about unsupported routing paths, not as an instruction to install
claudemix or a gateway.

The 2026-08-07 Claude Code checks provide current, bounded counter-evidence for
two ordinary no-proxy cases. They are useful behavior observations, not served
model proof and not a cross-runtime guarantee.

| Surface tested | Observed result | What it means |
|---|---|---|
| Agent-file foreign-model pin with no proxy | Loud failure: `Agent terminated early due to an API error` | The unsupported request did not proceed as a successful silent substitute in this test. |
| Inline model value outside the agent-tool schema | Schema validation rejected the value | The request was rejected before dispatch in this test. |
| `claude -p --model` invalid IDs (this machine; above) | Both invalid IDs exited 1; neither produced `ok` | The claude-cli lane failed loudly for these probes, while a valid `haiku` alias succeeded. |

Countermeasures use the existing evidence labels rather than an inferred model
identity:

| Existing label | Countermeasure when routing can substitute |
|---|---|
| `requested-pin` | Record the exact supported invocation, validate availability where the run warrants a consented probe, and keep the request distinct from a result. |
| `worker-self-report` | Preserve the claim for diagnosis, but never use an identity answer to resolve a routing dispute. |
| `native-inherited-unconfirmed` | Record the inheritance uncertainty; do not turn parent configuration, an agent file, or normal-looking output into a per-child model claim. |
| `runtime-metadata-confirmed` | Upgrade only from approved provider or CLI metadata that identifies the serving model; retain the raw event/source path and disagreements. |

If a request succeeds but deterministic serving metadata disagrees with it,
record both facts, classify the dispatch as a routing/transport failure, and
stop class-sensitive acceptance until a verified route or an explicitly
accepted reduced-assurance plan exists. Do not retry an unchanged request on
vibes.

## Current crew positioning

Treat every row as a quality/risk guide. Verify access before dispatch; provider publication and local cache presence do not grant access.

### Codex

The local cache on 2026-07-18 lists these seats. OpenAI positions Sol as flagship, Terra as balanced, and Luna as fastest/most affordable. `max` increases reasoning; `ultra` coordinates agents only where the supported seat and account expose it.

| Seat | Requested slug | Strengths | Limits | Upgrade signal |
|---|---|---|---|---|
| Sol | `gpt-5.6-sol` | Flagship judgment for ambiguity, integration, novel debugging, security-sensitive decisions, and final acceptance. | Higher latency/cost; excessive for crisp, deterministic work; availability must be verified. | Unresolved architecture, interacting failures, security/concurrency risk, or lead-owned final judgment. |
| Terra | `gpt-5.6-terra` | Balanced substantive implementation, tests, refactors, research, and review. | Do not treat it as a substitute for frontier ambiguity or final high-stakes synthesis. | Any unresolved design choice, conflicting evidence, or integration risk calls for Sol. |
| Luna | `gpt-5.6-luna` | Fast, affordable extraction, reconnaissance, inventory, mechanical edits, and narrow checks. | Weak fit for ambiguity, cross-file interaction, or unprescribed design judgment. | More than one material interpretation, interacting components, or an unclear failure calls for Terra or Sol. |

Use `ultra` only when automatic multi-agent coordination adds clear value, the active seat supports it, and the account exposes it. Keep older models only as verified compatibility or latency fallbacks; do not select them merely from familiarity.

Official source: https://openai.com/index/gpt-5-6/

### Claude

The following is official Claude positioning, not a statement that the user's CLI can select any row.

| Seat | Requested model | Strengths | Limits | Upgrade signal |
|---|---|---|---|---|
| Fable 5 | `fable` or `claude-fable-5` | Highest-capability long-running agent work. | Explicit Fable permission gate; expensive/distinct usage; verify access. | Use only when the task needs long-horizon frontier capability and the user authorizes it. |
| Opus 4.8 | `opus` or `claude-opus-4-8` | Complex agentic coding, autonomous debugging, and skeptical cross-family verification. | More expensive/slower than the workhorse; not a reason to bypass Fable permission. | Hard ambiguity, a high-risk verifier, or Sonnet evidence of a capability gap. |
| Sonnet 5 | `sonnet` or `claude-sonnet-5` | Speed/intelligence workhorse for substantive implementation and ordinary review. | Do not use as a mechanical default when ambiguity or long-horizon judgment dominates. | Novel debugging, difficult integration, or an unresolved safety/design choice calls for Opus. |
| Haiku 4.5 | `haiku` or `claude-haiku-4-5` | Fastest near-frontier seat for scans, extraction, and bounded mechanical work. | Limited margin for interacting systems and open-ended judgment. | Cross-component reasoning, ambiguous requirements, or a failed first pass calls for Sonnet or Opus. |
| Mythos 5 | `claude-mythos-5` | Fable-class capability in a limited defensive-cyber release. | Never route without explicit user request, verified access, and authorized defensive-security scope. | If all gates are not met, do not route; use an authorized alternative or report the limit. |

Use Fable only after the gate in `SKILL.md`: current-session user request or informed permission with a task-specific reason why Sol, Opus, or Sonnet is insufficient. Treat newer Claude IDs as dated releases rather than evergreen aliases.

Official sources:

- https://platform.claude.com/docs/en/about-claude/models/overview
- https://platform.claude.com/docs/en/about-claude/models/model-ids-and-versions
- https://platform.claude.com/docs/en/about-claude/models/choosing-a-model
- https://platform.claude.com/docs/en/about-claude/models/introducing-claude-fable-5-and-claude-mythos-5
- https://platform.claude.com/docs/en/about-claude/models/whats-new-claude-4-8
- https://platform.claude.com/docs/en/about-claude/models/whats-new-sonnet-5

## Route by residual judgment

Assess the judgment left after the ticket, not the domain's reputation:

1. List decisions the ticket has already fixed: algorithm, interfaces, data shape, files, constraints, examples, and exact checks.
2. List decisions still delegated: interpreting intent, selecting an approach, reconciling conflicts, debugging unknown causes, managing interacting components, or judging risk.
3. Set the capability class from the remaining material decisions, then apply a separate quality floor for impact and verification risk.

| Residual judgment | Typical route | Examples |
|---|---|---|
| Low | FAST | Enumerate files, extract fields, apply a prescribed local transformation, or implement supplied pseudocode with crisp checks. |
| Moderate | WORKHORSE | Complete a well-specified feature across known files, write tests for stated behavior, or review a bounded diff. |
| High | FRONTIER | Resolve ambiguous requirements, invent/revise an approach, investigate an unknown failure, integrate risky changes, or make final acceptance judgment. |

An algorithm-prescribing ticket is not judgment-heavy merely because its underlying domain is hard. A quality floor can still require stronger implementation review or final verification for security, safety, or irreversible impact; do not confuse that risk control with residual implementation judgment.

## Choose effort and break ties

Use `low`/`minimal` for deterministic scans, `medium` for bounded execution, `high` for cross-file logic and review, `xhigh` for hard debugging/architecture/security, and `max` for justified frontier reasoning. Do not route by line count or duration.

When several verified seats clear the bar, prefer: stronger expected result; cross-family independence for build versus verification; user/provider preference; lower quota pressure; then lower cost. Never promise savings from published API prices because subscriptions, limits, and billing modes differ.
