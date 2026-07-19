# Native Codex subagents

Use this lane when Codex exposes collaboration tools. A native child is a managed Codex thread, not a shell subprocess. Keep the parent responsible for coordination, model-evidence honesty, and final acceptance.

## Lifecycle and scope

Use the available equivalents of spawn, message, follow-up, list, wait, and interrupt. Set a stable lowercase task name, one complete [task contract](task-contracts.md), and the narrowest useful conversation fork. Use no forked turns for blind verification when the ticket contains all necessary context.

Native children share the workspace. Treat edits as immediately visible and never assign overlapping write sets concurrently. Discover the active thread cap, retain capacity for the lead and verifier, keep default spawn depth at one, and forbid worker fan-out. Repeat authorization and scope fences in every ticket because inherited tool access is capability, not permission.

## Record native model evidence honestly

Task names are bookkeeping only. Naming a child `terra_worker`, `sol-review`, or any other label does not select or change its model or effort.

Before dispatch:

1. Inspect the active spawn schema and session/runtime information.
2. Use a model/effort control only when that exact native surface exposes and accepts it; record `requested-pin`, not confirmation.
3. When the child may inherit a parent/runtime seat but no per-child runtime identity is available, label it `native-inherited-unconfirmed`.
4. Preserve `worker-self-report` only as the child's claim.
5. Add `runtime-metadata-confirmed` only when approved runtime metadata identifies the child's actual model; include effort only if exposed.
6. Use a model-pinned `codex exec` worker whenever exact seat control or evidence is required.

Do not abbreviate `native-inherited-unconfirmed` to a definitive model name. A parent model display, custom-agent file, accepted configuration, or task name can justify a request or inheritance hypothesis, not a claim that the child used that seat. See [models-and-routing.md](models-and-routing.md) for label meanings and precedence.

## Supervise and verify

After spawning, record canonical agent identity, task, write set, route, evidence label, and attempt in the authorized ledger. Continue only disjoint lead work; send missing facts promptly but do not casually change scope mid-turn. Wait for required reports, inspect shared-tree changes and raw evidence, and reuse an idle child only when fresh-context independence is unnecessary. Interrupt only for scope breach, obsolete work, unsafe action, or clear hang.

Do not treat a completion notification as success. Verify product criteria from the candidate and audit orchestration criteria separately. Confirm a terminal state for every native child before final acceptance.

## Blind native verification

Give a fresh child the original user task, lead-authored product criteria, candidate commit/diff or changed paths, read-only/no-delegation instructions, and a verdict format. Do not provide builder rationale, summary, or claimed test results. If inherited context prevents meaningful blindness, use an ephemeral Codex CLI or Claude CLI verifier instead.

## Custom agent files

Custom agent files can declare optional model and effort settings, but do not install or modify them merely to finish one task. Treat a selected profile setting as `requested-pin` until runtime metadata confirms use. If a user requests durable role profiles, make that a separate explicit configuration change and verify the active spawn surface can select it.

Official source: https://learn.chatgpt.com/docs/agent-configuration/subagents
