# Arm B pilot — the add-on cannot be arm B for a repair task

**Date:** 2026-09-11. One instance (`repair-ledger-730`), 6 requests, 203,186 quota tokens.
OpenClaw 2026.9.3, nine agents installed, all on `gemini-3.5-flash-lite`, `agentToAgent`
enabled, no channel bindings.

**Result: arm B ran as a single agent.** Not a worse panel — no panel.

```
agent DBs with any activity   1 of 9   (main)
requests                      6        (read x2, exec x2, edit x1)
agentToAgent steps            0
verdict                       PASS 11/11, edited
```

Arm B as invoked is arm A with a different system prompt. H1 is not testable in this
configuration, and 13–23 days of quota would have produced a comparison of two single
agents labelled as a panel-vs-agent test.

## Why, and why it is not fixable by invocation

Four findings, in increasing order of how fundamental they are.

**1. The shipped `agentToAgent` config does not load on this runtime.** The add-on writes a
directed edge list:

```json
"allow": [{"from": "*", "to": "planner"}, {"from": "ideator", "to": "critic"}, ...]
```

OpenClaw 2026.9.3's schema is `allow?: string[]` — "agent ids or `*` glob patterns; the
requesting and target agent must both match". The config is rejected outright. It was
written for an older runtime. **The restricted topology the add-on's README describes is not
expressible here**, so any valid translation is all-to-all, and H3's correlation structure
would have to be computed over what ran rather than what is documented.

**2. `agentToAgent` appears in no shipped prompt.** `grep -rl agentToAgent .agents/ soul.md`
returns nothing. No agent is told the tool exists or when to use it. Enabling it in config
makes it available; nothing makes it *used*.

**3. Delegation is driven by named workflow documents, and all four are research
processes.** `.agents/workflows/` ships `paper-pipeline.md` (phases measured in 1–2 weeks,
Surveyor → Scout → Planner → …), `brainstorm.md`, `daily-digest.md`, `rebuttal.md`. The
add-on's own next-step instruction is `openclaw chat planner`, then *"Start the
paper-pipeline workflow"*. Delegation is a scripted pipeline triggered by name.

**4. There is no repair-shaped workflow, and writing one would author the treatment.** A
bug-repair task matches none of the four. Arm B can only be made to deliberate by us writing
the delegation workflow — at which point arm B is a configuration we designed, which is
precisely what choosing a real deployed add-on was meant to avoid.

## What this does and does not establish

It does **not** say anything about deliberation, role specialisation, or H1. No comparison
was run and none is implied.

It does establish that **this add-on is a scripted research-paper pipeline, not a general
multi-agent scaffold**, and that pointing it at another task family yields one agent working
alone. That is worth knowing before the quota is spent, and it is consistent with the four
structural facts already recorded in the README: paper-oriented roles, per-agent isolated
workspaces, ~25% Chinese prompts, and now workflow-triggered delegation.

## Deviations made before concluding this

Five, all recorded in `sandbox/armb_entrypoint.sh`, all necessary to make it run *at all*
and none of them sufficient to make it deliberate: `--non-interactive` on `agents add`
(headless it created zero agents and exited 0), `jq` added to the image (its absence
silently skips the `agentToAgent` block), `OPENCLAW_HOME` left unset (or setup.sh writes to
a path the runtime never reads), the `agentToAgent` schema translation, and `agents.list` →
`agents.entries`. Every one of these fails silently and leaves a config that looks correct.

Sub-agents reaching the task by absolute path was verified working before it was relied on,
so each agent kept its own workspace and its own role prompt. That part of the plan was
sound; it simply was not the binding constraint.

## Cost

6 requests. The cheapest decisive result in this experiment so far, against a 13–23 day run
it makes unnecessary.
