# 007 pilot — observed facts

**Date:** 2026-09-10. **OpenClaw 2026.9.3 (1391f7c)**, image `openclaw-007` (node:24-bookworm-slim,
`npm i -g openclaw`, 1.61 GB). Backend: Groq free tier, `openai/gpt-oss-120b`.

Not a finding about agents. This is the harness check the README requires, and its headline is
that **the chosen backend cannot run 007 as designed.**

## The invocation

`openclaw agent exec` is the non-interactive path — one isolated headless turn, no gateway
daemon, no channels. Flags that matter: `--config`, `--cwd`, `--state-dir`, `--message-file`,
`--model provider/model`, `--code-mode`, `--local-model-lean`, `--timeout`, `--json`.

Three things the docs did not say, each of which cost a run to discover:

- **`--config` is mutually exclusive with both `--isolated` and `--auth-env-only`.** Pinning a
  config and using env-only credentials cannot be combined.
- **`apiKey: {source: "env", ...}` does not work headless.** Secret refs resolve through the
  gateway, which wants a paired device or a token; a config using one fails with
  *"failed to resolve secrets from the active gateway snapshot"*. The workaround is
  `sandbox/entrypoint.sh`: render the config inside the container from `$GROQ_API_KEY`, mode
  600, in the container's own `/tmp`. The key never lands on the host or in the repo.
- **Groq is not a built-in provider id** (built-ins include openai, anthropic, google, ollama,
  openrouter, together, xai, deepseek, zai). It works as a custom provider with
  `api: "openai-completions"` and `baseUrl: https://api.groq.com/openai/v1`.

## Trace export — target confirmed

State lives under `<state-dir>/agents/<agentId>/agent/openclaw-agent.sqlite`, as documented.
Two tables matter:

- `transcript_events(session_id, seq, event_json)` — `message`, `custom`, `session`,
  `model_change`, `thinking_level_change`.
- `trajectory_runtime_events(session_id, seq, run_id, event_json)` — a declared trace schema
  (`traceSchema: "openclaw-trajectory", schemaVersion: 1`) with `session.started`,
  `context.compiled`, `prompt.submitted`, `model.completed`, `trace.artifacts`,
  `session.ended`. **`model.completed` carries usage**, so tokens per call come from here.

That is the exporter's target, and it is richer than the JSONL fallback the docs mention. It
populates even on failed runs (25 events from a run that never edited a file), which is what
makes rate-limit failures auditable rather than invisible.

## Why the backend does not work

Groq's free tier is **8,000 TPM on every standard model** (verified from
`x-ratelimit-limit-tokens` on `openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `qwen/qwen3.8-27b`).
Only `groq/compound-mini` is higher at 70,000 TPM — and that is Groq's own agentic pipeline,
which would put an agent system inside the agent system under test. Unusable here for that
reason alone.

Against that cap:

| configuration | request size | outcome |
|---|---|---|
| default tool surface, trivial message | **16,707 tokens** | 413 — one turn is 2× the whole per-minute budget |
| `--local-model-lean --code-mode code` | fits | 200, but see below |
| `--local-model-lean --code-mode direct`, real task | ~6.8–7.2k per turn | 200s interleaved with 429s |

So a single agent turn consumes most of a minute's budget: **≈1 turn per minute sustained.**

- Arm A needs perhaps 5–15 turns per instance → 5–15 min/instance → 3–10 h for n=40.
- Arm B is nine agents with an orchestrator → 30–60+ turns/instance → **20–40 h**, and it would
  spend most of that in backoff.

**This is not slowness, it is a confound.** 007 predicts arm B loses. On this backend arm B
would also hit rate limits far more often than arm A, so a loss would be unattributable —
exactly the contamination flagged before the build. Do not run the comparison here.

## One more incompatibility, worth keeping

With `--code-mode code`, gpt-oss-120b emitted an `exec` tool call missing the required `code`
property and Groq rejected the payload:
*"parameters for tool exec did not match schema: missing properties: 'code'"*.
`--code-mode direct` validates. Tool-schema compliance is model-specific, which is the
tool-using analogue of the `format_ok` column from 001 — and an argument for recording it per
arm rather than assuming it.

## What is still unpinned

The two questions that gate H3 need a working backend and were not reachable:

- whether `--model-map` holds one model across all nine agents;
- what an `agentToAgent` message looks like in `trajectory_runtime_events`. **H3 is not
  computable until that is known**, because correlated failure has to be measured across agents
  that talked, and an inter-agent message has to be distinguishable from a tool call.

## Cost so far

Eight API calls, all inside the free tier. No result claimed, none implied.
