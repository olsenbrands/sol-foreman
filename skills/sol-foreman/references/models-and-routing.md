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
