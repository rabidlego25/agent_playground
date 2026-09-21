# agent_playground

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
- **Check a stored baseline's provenance before reusing it.** `f035461` (2026-08-30) fixed a
  shortcut in `multi_hop` where the gold answer was the graph root, so "walk up until you cannot"
  scored ~1.00 without counting a hop. It quarantined two probes into `results/preshortcutfix/`
  and missed four: `probe_distractor_load.jsonl` (250 rows), `probe_variance_floor.jsonl` (240),
  `probe_name_scramble.jsonl` (120), `probe_order_sensitivity.jsonl` (120). These are pre-fix and
  their accuracies are not comparable to anything run after. Signature: post-fix `multi_hop`
  records carry an `above` key in `config.difficulty`; pre-fix records do not.

## Constraints

- Machine: MacBook Pro 14" M1 Pro, 16 GB unified memory. MPS, not CUDA. Local models cap out around 7B–14B quantized.
- Claude access is via a Pro subscription (usage-limited) — design for small, replayable sweeps rather than large fan-outs.
- Model scope is **not** Claude-only: use whichever accessible model fits the role, and say why.
- **Context is served at 4096 tokens unless you ask for more.** ollama 0.30.10 ignores the model
  card and defaults `num_ctx` to 4096 — llama3.1 advertises 131,072 and is served at 1/32 of it
  (measured 2026-09-21). No result before that date was affected: the largest local prompt on
  file is 1,307 tokens. Any experiment that varies or depends on context **must** pass `num_ctx`
  through `lib.models.Ollama` and record it in `config`.
- **The practical context ceiling is ~32k, set by memory, not by the model card.** llama3.1's KV
  cache measured 128 KiB/token, so its 131k window extrapolates to ~16 GiB on a 16 GB machine.
  qwen2.5 at `num_ctx=32768` is 6.4 GB resident vs 5.3 GB at 4096, allocated at load. Reserving a
  window is cheap; filling it is not — prefill runs ~190s at 30k tokens (`experiments/012-context-length/`).

## Currently available models (verified 2026-08-30)

- Claude, via Claude Code itself (Opus 5 / Sonnet 5 / Haiku 4.5) — subscription-metered.
- Local via `ollama`: `qwen2.5:latest` (7B), `llama3.1:latest` (8B), `mistral:7b`. ~13.3 GB on disk.
- No third-party API keys are set in the environment. Adding Groq/Google AI Studio/Cohere keys
  costs $0 and no card, and would widen the roster to genuinely independent families.

**Measured solo accuracy** on `multi_hop` depth 4, bare prompt, n=195 (2026-08-30):
qwen2.5 **0.51**, llama3.1 **0.22**, mistral:7b **0.18**. Two consequences, both learned the
expensive way in `experiments/003-mixed-panel/`:

- **Do not treat the local models as a peer panel.** A vote among them lands *below* qwen2.5
  alone (0.43, p=0.007) because two of three sit under the Condorcet competence threshold.
- **Size is not capability.** llama3.1 8B is the largest local model and the second weakest.
  Match panels on measured accuracy, never on parameter count.

Every figure above is on the bare prompt, which `experiments/001-deliberation/` arm B showed is
worth **0.21** to a single call. Solo rates are floors, not ceilings.

## Tooling

`uv` (preferred for Python), Python 3.14, node/npm, docker, ollama, git.
GitHub: `git@github.com:rabidlego25/agent_playground.git` (public, branch `main`).

## Writing style (assistant output and notes)

Optimise for information per token, not for looking thorough. Length is not the target — a long
argument that is all load-bearing is fine; a short one padded with rhetoric is not.

**Cut:**
- Bolded lead-ins on every paragraph. Bold is navigation in a long answer, not decoration.
- Aphorisms and punchy closers. They make a weak claim sound settled. If a compression is genuinely
  reusable it belongs in `notes/`, not in chat.
- Restating or complimenting the question before answering it ("that's a sharper idea than it
  sounds", "your instinct is right").
- Triads padded to three items when there are two.
- Narrating reasoning that was not asked for. The conclusion is the product; the path usually isn't.
- Status lines appended reflexively when nothing has changed.

**Prefer:**
- The answer in the first sentence.
- A number, date, or `file:line` instead of an adjective.
- "I don't know" in one sentence, not a framed paragraph of hedging.
- Stating disagreement flat rather than sandwiching it.
- Unverified claims marked as unverified, with what would verify them.

**Why this is a project convention and not a preference:** the failure mode this guards against is the
same one that produced the oracle bug (see `notes/2026-08-29-oracle-format-confound.md`) — output that
is confident, well-formatted, plausible, and wrong. Rhetorical polish raises the cost of catching that.
Whether it *actually* does is testable; see `experiments/002-rhetoric-vs-information/`.
