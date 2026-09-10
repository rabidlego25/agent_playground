# What an agentic engineer should be expected to know about LLMs

**Date:** 2026-09-10. Written as a reference, not a tutorial. Organised by unit of analysis —
token, call, context, loop, panel, evidence — because that is the order in which the failure
modes stop being about the model and start being about the system around it.

Numbers attributed to this repo are from `experiments/001`–`006`, `multi_hop` depth 4, n=195,
qwen2.5 7B unless stated. They are cited because they are measured here and re-checkable, not
because they generalise.

## 1. Token

A language model is a conditional distribution over the next token. Everything else — chat,
tools, agents — is a wrapper around sample-append-repeat. Capabilities are properties of that
distribution, and so are the failures.

- **Tokens are not words.** BPE merges make a rare identifier or a long number cost 5–15 tokens;
  the same word with and without a leading space are different tokens. This is why
  character-level tasks (count the letters, reverse the string) fail for reasons that have
  nothing to do with reasoning, and why budgets are counted in tokens, never characters.
- **Sampling knobs, and what they do to the distribution.** `temperature` scales logits before
  the softmax — below 1 sharpens, above 1 flattens. `top_p` / `top_k` / `min_p` truncate the tail
  before sampling; they bound the worst token, not the typical one. Repetition and frequency
  penalties distort the distribution in ways that damage code and structured output — prefer stop
  sequences. Temperature is also the diversity knob for ensembling (§5): it sets how much
  independent error there is to average over.
- **Logprobs are the cheapest signal in the stack**, and most agent code throws them away. They
  give a confidence proxy for routing and abstention, a way to see the model being forced into a
  token by a bad schema, and an estimate of how concentrated the answer distribution is without
  paying for k draws.
- **Verbalised confidence is not a probability.** "I'm 90% sure" is a stylistic feature of the
  text, not a calibrated estimate, and it does not track logprob.

## 2. Call

- **Attention is O(n²) in compute; the KV cache is linear in n.** Doubling the context roughly
  quadruples prefill and doubles cache memory. On a 16 GB machine the memory is what kills you
  first. GQA/MQA exist to shrink the cache, which is why head counts differ from what you'd
  guess from d_model.
- **The advertised context length is a maximum, not a runtime setting.** Local example measured
  2026-09-10: `qwen2.5:latest` reports 32768, and ollama loaded it at `num_ctx` 4096. Always
  check what was actually allocated.
- **Model size is not capability.** Same tasks, bare prompt, 2026-08-30: llama3.1 8B **0.22**,
  qwen2.5 7.6B **0.51**, mistral 7.2B **0.18**. The largest local model is the second weakest.
  Quantisation is a separate axis and costs quality unevenly across task types.
- **The prompt is the highest-leverage variable, by a wide margin.** Same model, same 195 tasks
  (001): imposed output notation **0.27**, bare **0.51**, one line of "work through it step by
  step" **0.72**. The whole configuration axis — one agent, seven agents, agents that talk —
  spanned 0.51–0.63 on the same tasks. Any configuration effect measured below the prompt
  ceiling is a measurement of how much that configuration compensates for a bad prompt.
- **Test-time compute is a real axis but not the same axis as sampling.** Tokens spent reasoning
  inside one call and tokens spent on k independent calls both buy accuracy, and they do not
  compose linearly.
- **Determinism is not available.** Identical prompt, identical seed, temperature 0 still varies,
  because floating-point reduction order depends on how requests batch on the server. Design for
  distributions; fix seeds anyway for the part you do control.
- **Structured output and tool calls are constrained decoding.** The schema is part of the prompt
  whether or not you think of it that way: field names and descriptions carry the same weight as
  instructions. Over-constraining costs accuracy — imposing an answer-only notation cost 0.24 in
  001.
- **Prefix caching makes context order a cost decision.** Stable content (system, tools,
  few-shot) first, volatile content last, or every turn invalidates the cache.

## 3. Context

- **Position matters more than it should.** Instructions at the start or the end of a long
  context are followed more reliably than the same instructions in the middle, and long-context
  retrieval degrades in the middle of the window.
- **More context is not better context.** Irrelevant retrieved material lowers accuracy;
  distractor load is a measurable axis, not a free one (`tests/probe_distractor_load.py`).
- **Compaction is lossy in a biased direction.** It keeps conclusions and drops the search that
  produced them — cheap for a reader who agrees, expensive for one who has to revisit the
  decision. This is the open hypothesis in `experiments/002-rhetoric-vs-information/` (H3).
- **Everything the model reads is untrusted.** Tool output, retrieved documents, file contents,
  web pages, and other agents' messages are all injection surfaces. The trust boundary is not
  system-prompt-versus-user; it is tokens you authored versus tokens something else authored.
  An agent with shell access and a fetch tool is a confused deputy by default.

## 4. Loop

An agent is a call in a loop with tools and state. The dominant failure is not a wrong answer,
it is compounding: 0.95 per step is 0.36 over 20 steps. Reliability work for agents is mostly
about step count, checkpointing, and verification — not about model choice.

- **Verification asymmetry is the lever.** Where checking is cheaper than doing (tests, types,
  a programmatic oracle), retries are productive. Where there is no checker, a retry just
  resamples the same error mode.
- **Instrument the silent failures.** Truncation at `max_tokens` is indistinguishable from a
  wrong answer unless you record whether the cap bound. Format failure is indistinguishable from
  reasoning failure unless you score them separately — this repo's first result was fake for
  exactly that reason: the oracle scored narration as wrong and read llama3.1 at 2/30 on
  single-hop lookups (`notes/2026-08-29-oracle-format-confound.md`). Report a compliance column
  beside accuracy. The oracle is part of the experiment and needs its own tests.
- **Tool errors come back as strings**, and the model will happily reason over an error message
  as if it were data.
- **Store full traces, not verdicts.** Every re-analysis you will want later is impossible
  without the raw responses, and replay is free where re-running is not.

## 5. Panel

Two things get called "multi-agent" and they behave in opposite directions.

- **Ensembling** — k independent samples, majority vote — works. k=7 bought +0.113 over a single
  call on the bare prompt and **+0.195** on the reasoning prompt (004).
- **Deliberation** — agents that read each other — does not. At matched tokens it was 1.85× the
  cost of independent sampling for identical accuracy (001), and at the prompt ceiling it is
  significantly *worse* than not communicating: 0.71 vs 0.86, p<0.0001, at 1.2× the cost (004).
  In 005 it cost the strongest panel member −0.123.

What a vote buys is error independence, and the governing quantity is
**c = P(a second draw repeats the first | the first is wrong)**. A better prompt lowered it
0.339 → 0.239; mixing model families lowered it to 0.211; the two stack. Communication raises
it — which is the mechanism by which deliberation destroys the thing ensembling pays for.

- **Condorcet still applies.** Majority voting helps only when members sit above ~0.5 with
  roughly independent errors; below that, adding voters makes it worse. Measured: a three-way
  local panel (0.51 / 0.22 / 0.18) votes **0.43** — below its best member alone, p=0.007 (003).
  Match panels on measured accuracy, never on parameter count.
- **Independence without competence buys nothing.** 005 got c to 0.211 across families and the
  vote still lost to its best member by 0.09 (p=0.0001).
- **Working order:** fix the prompt, then ensemble without communication, and do not deliberate.
- **Check saturation before paying for k.** On the bare prompt the curve flattened by k=3; on the
  reasoning prompt k=5 and k=7 both still paid. Where it saturates is a property of the prompt
  (006 is measuring the asymptote now, with the k=15 prediction pre-registered at 0.89).

## 6. Evidence

- **Report n and an interval.** Wilson, not the normal approximation, at these n.
- **Compare paired, on identical instances** (exact McNemar). Instance variance dominates:
  this repo's calibration puts task-set variance at **0.163** against run-to-run **0.050**. An
  unpaired comparison of two configurations at n=100 is mostly reporting which tasks you drew.
- **Know the noise floor before believing an effect.** The multi-agent literature reports gains
  of 0.05–0.10 — smaller than the prompt-induced spread inside the same experiments.
- **Pre-register the number** when the analysis has freedom in it. An estimator that explains
  past results is cheap; one that predicts a number you have not drawn yet is not.
- **Generated tasks with programmatic oracles** beat collected benchmarks on contamination
  resistance, difficulty control, and n at zero token cost, at the price of external validity.
  Say which you have.
- **LLM-as-judge inherits the judge's biases**, including a preference for confident,
  well-formatted answers. Same-family judge and candidate measures style agreement in part.
- **Date every result**, with the model id. An undated number is unreadable in six months.

## Commonly believed, wrong

| Belief | What the measurement says |
|---|---|
| Bigger model is better | llama3.1 8B 0.22 vs qwen2.5 7.6B 0.51 |
| Temperature 0 is deterministic | Batch-dependent reduction order; it is not |
| More agents is better | Below the competence threshold, more voters is worse; communicating is worse still |
| A long context window means the context gets used | The window is an allocation, not an ability |
| "Embedding" is the vector you put in a vector DB | In a model spec it is d_model, the hidden width |
| The model is the variable | Prompt moved this repo's number 0.45; model choice 0.33; configuration 0.12 |

## Half-life

**Re-check every few months:** model ids, pricing, context lengths, tool-calling APIs, which
model is strongest, quantisation quality, reasoning-token behaviour.

**Stable:** tokenisation consequences, the attention/KV cost shape, position effects, Condorcet
arithmetic, compounding over steps, injection as a trust boundary, and the measurement
discipline in §6.
