# agent_research

A long-term scratchpad for empirical work on agentic systems: testing agent
configurations, analyzing and building benchmarks, and pushing on novel ideas
about how agents perform best in workflows. Not a product. Started 2026-08-29.

## Layout

- `experiments/` — one directory per experiment, named `NNN-slug/` (e.g. `001-role-specialization/`).
  Each contains `README.md` (hypothesis, method, result), the code, and a `runs/` dir.
- `benchmarks/` — benchmark harnesses and analyses of existing suites (SWE-bench, GAIA, τ-bench, etc.).
- `lib/` — shared, provider-agnostic code. Model access goes through one adapter layer here.
- `notes/` — ideas, theory, reading notes, open questions. Speculation is welcome and belongs here.
- `results/` — raw run artifacts (JSONL traces, metrics). Append-only; never edit a past run in place.

## Conventions

- **Every experiment states a hypothesis before it runs.** A README with only results is a log, not an experiment.
- **Date everything.** Absolute dates, not "last week". Model capabilities move; an undated result is unreadable in six months.
- **Traces are the primary artifact.** Log full request/response traces to `results/` as JSONL so a run can be
  re-analyzed without re-paying for it. Prefer replay over re-run.
- **Provider-agnostic by default.** No vendor SDK calls scattered through experiment code — go through `lib/`.
- **Small N, stated.** Report n and variance. A single run of an agent config is an anecdote.

## Constraints

- Machine: MacBook Pro 14" M1 Pro, 16 GB unified memory. MPS, not CUDA. Local models cap out around 7B–14B quantized.
- Claude access is via a Pro subscription (usage-limited) — design for small, replayable sweeps rather than large fan-outs.
- Model scope is **not** Claude-only: use whichever accessible model fits the role, and say why.

## Currently available models (verified 2026-08-29)

- Claude, via Claude Code itself (Opus 5 / Sonnet 5 / Haiku 4.5) — subscription-metered.
- Local via `ollama` (installed, server not running; `ollama serve` to start): `llama3.1:latest` (8B), `qwen2.5:latest` (7B). ~8.9 GB on disk.
- No third-party API keys are set in the environment. Adding OpenAI/Gemini/Groq/OpenRouter keys would widen the comparison set.

## Tooling

`uv` (preferred for Python), Python 3.14, node/npm, docker, ollama, git. This folder is not yet a git repo.
