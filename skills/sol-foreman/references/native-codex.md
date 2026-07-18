# Native Codex subagents

Use this lane when Codex exposes collaboration tools. A native subagent is another Codex thread managed by the parent runtime, not a shell subprocess.

## Lifecycle

The exact names vary by surface. Use the available equivalents of:

- spawn an agent with a stable task name, bounded message, and minimal context;
- send a message to a running agent;
- give an idle agent a follow-up task;
- list agents and inspect state;
- wait for mailbox updates or completion;
- interrupt a turn when it must stop.

Keep the parent responsible for coordination and acceptance.

## Spawn well

Set:

- a stable lowercase task name;
- one complete ticket from [task-contracts.md](task-contracts.md);
- the narrowest useful conversation fork.

Use no forked turns for independent blind verification when the ticket carries all required context. Use recent or full turns only when reconstructing the context would be error-prone and independence is not the goal.

Native children share the workspace. Treat all edits as immediately visible. Never assign overlapping write sets concurrently.

## Respect runtime limits

Discover the active thread cap instead of assuming one. Keep capacity for the lead and for a verifier. Default Codex configuration may allow more threads than the current product surface or team runtime.

Keep default spawn depth at one. Workers do not spawn workers. Recursive fan-out makes cost, permissions, and partial failure harder to reason about.

Subagents inherit important parent runtime conditions, including available tools and often sandbox or permission settings. Tool access is capability, not authorization; repeat the task's fence in the ticket.

## Be honest about model control

Some Codex surfaces support custom agent files or model settings; some collaboration tool schemas expose only task, message, and context. Before assigning a seat:

1. Inspect the spawn tool schema and session model information.
2. Pin model and effort only when the active surface exposes a supported control.
3. If no control exists, label the child seat `inherited` or `unconfirmed`.
4. Use a model-pinned `codex exec` worker when exact routing is necessary.

Never infer that a task name such as `terra_worker` changed the model.

## Supervise

After spawning:

1. Record the canonical agent identity and task in the ledger.
2. Continue only disjoint lead work.
3. Send missing facts promptly; do not change scope casually mid-turn.
4. Wait for all required results before synthesis.
5. Inspect the child's evidence and shared-tree changes.
6. Reuse an idle child with a follow-up only when fresh-context independence is not required.
7. Interrupt only for scope breach, obsolete work, unsafe action, or clear hang.

Do not treat a completion notification as task success.

## Blind native verification

Use a fresh child with:

- the original user task verbatim;
- the lead-authored acceptance criteria;
- the candidate commit/diff or changed paths;
- read-only instructions and explicit bans on edits or delegation;
- required verdict format.

Do not include the builder's rationale, summary, or claimed test results. If the native child necessarily inherits contaminating context, use an ephemeral Codex CLI or Claude CLI verifier instead.

## Custom agent files

Current Codex documentation supports personal custom agents under `~/.codex/agents/` and project agents under `.codex/agents/`. A TOML file can define:

- `name`;
- `description`;
- `developer_instructions`;
- optional `model`, `model_reasoning_effort`, `sandbox_mode`, and other supported config.

Do not install or modify custom agents merely to finish one task. If a user wants durable role profiles, create them as a separate, explicit configuration change and verify that the active spawn surface can select them.

Official source: https://learn.chatgpt.com/docs/agent-configuration/subagents
