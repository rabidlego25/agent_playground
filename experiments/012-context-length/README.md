# 012 — What does a longer context cost, in speed and in accuracy?

**Status 2026-09-21:** pre-registered; anchor cell run, remaining five cells running.
Zero API cost — local ollama only.

## Why

Every local result in this repo was produced at a 4096-token window, and nobody chose it.
`lib/models.py` never set `num_ctx`, so ollama served its own default and the model card was
irrelevant: llama3.1 advertises 131,072 and was served 4,096 — 1/32 of its trained window.
Measured 2026-09-21 on ollama 0.30.10 (`OLLAMA_CONTEXT_LENGTH:0`, `ollama ps` → `CONTEXT 4096`,
loader log `n_ctx_seq (4096) < n_ctx_train (131072)`).

Nothing on file is corrupted by this: the largest local prompt across every trace in the repo
is 1,307 tokens, roughly 3× under the ceiling. The question is what happens if we raise it.

## The variable, and the thing it is usually confounded with

"Raise the context" names two different costs:

- **allocation** — how large a KV cache is reserved (`num_ctx`). Paid once, at load, in memory.
- **occupancy** — how many tokens the prompt actually spends. Paid on every call, in prefill.

`num_ctx` is therefore held at **32768 in every cell but the anchor**, and only the prompt
grows. The single variable is occupancy. Two cells exist to keep it that way:

- **anchor-4k/pad0** — `num_ctx=4096`, no padding. The configuration every earlier result in
  this repo ran under, and the baseline everything else is paired against.
- **ctx32k/pad0** — `num_ctx=32768`, no padding. The **allocation control**. If this differs
  from the anchor, reserving the window costs something before a single extra token is read.

## Method

One model, `qwen2.5:latest` — the only local model with the dynamic range to show a drop
(0.51 solo at depth 4; llama3.1 at 0.22 and mistral at 0.18 have no headroom, and a null from
them would be indistinguishable from their floor). `multi_hop`, depth 3, 6 distractors,
temperature 0.0, `num_predict` 400.

Seeds **2000–2019**, n=20, **the same instances in every cell**, which makes the design paired
and McNemar the right test.

**The anchor was meant to be a replication check and became a correction instead.** This block
is the one `tests/probe_distractor_load.py` records at **0.88 (n=50, 20/20 on these exact
seeds)** under `distractors=6`. The anchor cell, run first on 2026-09-21, scored **0.55
(11/20)** — disagreeing on 9 of 20 identical seeds, all in the same direction. The stored probe
is pre-`f035461`: it ran under the `multi_hop` shortcut bug, where the gold answer was the
graph root and "walk up until you cannot" scored without counting a hop. Its records carry no
`above` key in `difficulty`, which is the data-level signature of the old generator. **0.55 is
the honest current number; 0.88 was never a property of the task as it exists now.** The rest
of this README's design was written against 0.88 and has been corrected here rather than
silently — the pre-registered predictions below are unchanged, because none of them depended
on the baseline's value except H4's power note, which is restated for 0.55.

The reasoning task is byte-identical across cells. What grows is neutral filler prose placed
**before** it — warehouse-inventory sentences carrying no personal names, none of the task's
relational vocabulary (`reports`, `above`, `level`, `manager`), and varied rather than one
sentence repeated, since a model attending over 27k tokens of an identical block is not a
model attending over 27k tokens of text. Any accuracy difference is therefore attributable to
prompt length, not to task difficulty.

| cell | `num_ctx` | filler | prompt tokens (target) |
|---|---|---|---|
| anchor-4k/pad0 | 4,096 | none | ~100 |
| ctx32k/pad0 | 32,768 | none | ~100 |
| ctx32k/pad2k | 32,768 | 2k | ~2,100 |
| ctx32k/pad6k | 32,768 | 6k | ~6,100 |
| ctx32k/pad14k | 32,768 | 14k | ~14,100 |
| ctx32k/pad27k | 32,768 | 27k | ~27,100 |

The filler's chars-per-token ratio is **measured against this model's tokenizer at run time**,
not assumed — a guessed 4.0 would miss the 27k target by thousands of tokens. The x-axis of
every result is the measured `tokens_in` on each call, which the trace records; the targets
above are only how the prompt was built.

**Truncation guard.** ollama drops from the *front* of an over-long prompt, and the task sits
at the *end*, so a truncated call still answers — it just answers with less context than its
label claims. That is a silently mislabelled cell, which is worse than a crash. The run aborts
if mean `tokens_in` exceeds `num_ctx - 400`.

## Pre-registered predictions

**H1 — prefill cost is superlinear in prompt length.** Prefill throughput at ~27k tokens is at
least 25% below its rate at ~2k. *Not a blind prediction*: an n=1 pilot on 2026-09-21 already
measured 244 → 158 tok/s (−35%) across that range. The sweep puts n=20 and a median on it
rather than discovering it. Falsified by throughput flat within ±10%.

**H2 — decode degrades too, but far less.** Output throughput at 27k is 10–50% below the
anchor. Pilot (n=1, 64 output tokens): 2.42s → 3.63s, so decode is the smaller cost and is
predicted to stay so. Falsified by decode degrading proportionally to prefill.

**H3 — allocation is close to free.** `ctx32k/pad0` matches the anchor on accuracy (no
McNemar discordance beyond chance) and on per-call wall time to within 1s, once model load is
excluded. Falsified by a measurable accuracy or latency gap, which would mean the window
itself, not its contents, is the cost.

**H4 — accuracy holds.** Accuracy at 27k is within noise of the anchor. The task sits at the
end of the prompt, the filler is semantically unrelated to it, and recency is the easiest
position for a transformer to attend to. **This is the prediction most worth being wrong
about**, so its falsifier is stated in advance: a paired drop with McNemar p < 0.05. From a
0.55 anchor at n=20 that needs roughly a 0.30 absolute drop (11/20 → 5/20) to reach p < 0.05,
so a null here is weak evidence and is recorded as such rather than as "long context is free".
The upside is that a 0.55 baseline has range in *both* directions: unlike the 0.88 the design
was originally written against, an improvement would also be visible.

**H5 — format compliance breaks before reasoning does.** If anything degrades first it is
`fmt_ok` (the `ANSWER: <name>` final line), not correctness, because instruction-following is
the commonly reported first casualty of long context. Falsified by accuracy dropping while
`fmt` holds at 1.00.

## Limits, stated before the run rather than after

- **One position.** The task is always last. A null result here says *trailing-position
  reasoning survives irrelevant context*, not *context is free*. The middle-position variant
  — the "lost in the middle" shape — is the follow-up this design deliberately does not buy,
  and `run.py` supports it with a padding split.
- **One model, one family, one depth.** No claim transfers to llama3.1, mistral, the Gemini
  tier, or to a task whose reasoning is spread through the context rather than concentrated
  at its end.
- **n=20** is powered for a large effect only. Both the interval and the McNemar p are
  reported; neither is a substitute for the other.
- **Memory sets the real ceiling, not the model card.** llama3.1's KV cache measured 512 MiB
  at 4,096 tokens — 128 KiB/token — so its 131,072 window extrapolates to ~16 GiB of KV on a
  16 GB machine and is unreachable. ~32k is the practical cap for the whole local roster,
  which erases llama3.1's paper advantage over qwen2.5 and mistral entirely.

## Result — 2026-09-21

Ran `qwen2.5:latest`, five cells, n=20 each, paired on seeds 2000–2019. 81 minutes of model
time. The sixth cell (`ctx32k/pad27k`) was **not run**; see the calibration note below.

### Correction: the cell labels understate occupancy by 2.13×

`calibrate()` (`run.py:108`) returned 10.167 chars/token. The true value for this filler under
qwen2.5's tokenizer is ~4.77. Every padded cell therefore carries 2.13× its nominal target:

| cell | nominal target | measured median `tokens_in` |
|---|---|---|
| `anchor-4k/pad0` | ~155 | 155 |
| `ctx32k/pad0` | ~155 | 155 |
| `ctx32k/pad2k` | ~2,155 | **4,418** |
| `ctx32k/pad6k` | ~6,155 | **12,911** |
| `ctx32k/pad14k` | ~14,155 | **29,900** |

Cause: `calibrate()` sends an ~8,700-token block and divides `len(block)` by `c.tokens_in`
(`run.py:116`), but the backend was still at `num_ctx=4096` for that call. ollama truncated the
block and reported the cap back, so the ratio was computed against 4,096 tokens instead of
~8,700. 4,096 × 2.13 ≈ 8,700. The measurement measured the ceiling, not the tokenizer.

Two consequences, both stated rather than papered over:

- **Everything below is read on measured `tokens_in`, never on the cell label.** The labels are
  kept as written so the traces and this README agree with `results/012_context.jsonl`.
- **`ctx32k/pad14k` *is* the pre-registered 27k cell**, at 29,900 tokens — 91% of the window and
  a 193× span from the anchor. `ctx32k/pad27k` would have built ~57,500 tokens of filler against
  a 32,768 window, been truncated by ollama, and tripped the post-cell `TRUNCATED` guard after
  ~73 minutes of compute. The sweep was stopped deliberately after `pad14k` landed its 20th row.
  `results/012_context.jsonl` holds five cells at n=20 and zero `pad27k` rows.

The fix is one line in `calibrate()` — calibrate against a block short enough to fit 4,096
tokens, or set `num_ctx` before calibrating. Not applied here, because re-running under a
corrected ratio would overwrite an 81-minute sweep whose occupancy axis is already measured
and already spans the intended range.

### Speed (median per call)

| cell | prompt tok | prefill s | prefill tok/s | decode s | out tok/s | wall s |
|---|---|---|---|---|---|---|
| `anchor-4k/pad0` | 155 | 0.49 | 315 | 4.58 | 25.9 | 5.24 |
| `ctx32k/pad0` | 155 | 0.49 | 315 | 4.53 | 26.2 | 5.16 |
| `ctx32k/pad2k` | 4,418 | 19.16 | 231 | 4.25 | 24.0 | 23.84 |
| `ctx32k/pad6k` | 12,911 | 65.30 | 198 | 5.35 | 21.2 | 71.02 |
| `ctx32k/pad14k` | 29,900 | 189.75 | 158 | 6.78 | 17.0 | 197.08 |

### Accuracy (n=20, paired, McNemar vs `anchor-4k/pad0`)

| cell | prompt tok | acc | 95% CI | fmt | anchor-only | cell-only | p | agree/20 |
|---|---|---|---|---|---|---|---|---|
| `anchor-4k/pad0` | 155 | 0.55 | [0.34, 0.74] | 1.00 | — | — | — | — |
| `ctx32k/pad0` | 155 | 0.55 | [0.34, 0.74] | 1.00 | 0 | 0 | 1.000 | 20 |
| `ctx32k/pad2k` | 4,418 | 0.70 | [0.48, 0.85] | 1.00 | 4 | 7 | 0.549 | 9 |
| `ctx32k/pad6k` | 12,911 | **0.85** | [0.64, 0.95] | 1.00 | 1 | 7 | **0.070** | 12 |
| `ctx32k/pad14k` | 29,900 | 0.80 | [0.58, 0.92] | 1.00 | 3 | 8 | 0.227 | 9 |

### Verdict against the pre-registered predictions

**H1 — prefill cost is superlinear. CONFIRMED.** Prefill throughput falls 231 → 158 tok/s
between 4.4k and 29.9k tokens, −32%, clearing the pre-registered ≥25% threshold; against the
155-token anchor it is 315 → 158, −50%. The falsifier (flat within ±10%) is not close. In
absolute terms prefill grows 0.49s → 189.75s, a factor of 387 for a factor of 193 in length.

**H2 — decode degrades far less. SPLIT: the magnitude holds, the "far less" does not.** Decode
throughput falls 25.9 → 17.0 tok/s, −34%, inside the predicted 10–50% band. But the stated
falsifier was *decode degrading proportionally to prefill*, and over the 4.4k → 29.9k range it
very nearly does: prefill −32%, decode −29%. On throughput ratio the two costs are the same
shape. What separates them is absolute time: prefill 0.49s → 189.75s (387×) against decode
4.58s → 6.78s (1.48×). Decode is the smaller cost because there are ~116 output tokens and
29,900 input ones, not because its per-token rate holds up better. **H2 as written conflated
those two claims and should not be reused in that form.** Median output length is flat across
cells (118 → 116 tokens), so this is not an artifact of longer generations.

**H3 — allocation is close to free. CONFIRMED, and it is the cleanest result here.** Reserving
a 32,768-token window and leaving it empty changed nothing: accuracy 0.55 vs 0.55, **per-seed
agreement 20/20**, prefill identical at 0.49s, wall 5.16s vs 5.24s. Not merely the same rate —
the same instances right and the same instances wrong. The KV cache is allocated at load, so
the cost of a large window is memory (measured: 6.4 GB resident at `CONTEXT 32768` vs 5.3 GB at
4096, `ollama ps`, 2026-09-21), not latency and not accuracy. Whatever the padded cells show,
it is occupancy doing it.

**H4 — accuracy holds. NOT FALSIFIED, and wrong in an unpredicted direction.** The falsifier
was a paired drop at p < 0.05. There is no drop. Accuracy *rose* with occupancy, peaking at
0.85 at 12,911 tokens and still 0.80 at 29,900. At `pad6k` seven seeds flipped wrong→right and
one flipped right→wrong — a 7:1 asymmetry, exact two-sided p = 0.070. That does not clear 0.05
and **is not being recorded as an effect.** It is recorded as the most interesting thing the
sweep produced and the reason for a follow-up.

The obvious explanation — irrelevant filler acts as a length prior that buys more deliberation —
is weakly contradicted by the output lengths: medians are flat (118 → 116). The one real signal
is that the shortest completions disappear under padding (min 45 → 74 tokens, mean 103 → 117).
Alternatives not yet separated: (a) n=20 noise, which 0.070 is entirely consistent with;
(b) the filler makes the task block salient as a distinct, recent region rather than as the
whole prompt; (c) something specific to this filler's register. Distinguishing these needs a
second padding vocabulary and n≥60, which is experiment 013, not a claim here.

**H5 — format compliance breaks first. UNTESTED.** `fmt_ok` is 1.00 in all five cells,
including at 29,900 tokens. Nothing degraded, so the prediction's premise never triggered. It
is neither confirmed nor falsified.

### What this does and does not license

It licenses one operational rule: on this machine, a large `num_ctx` is free to *reserve* and
expensive to *fill*, and the bill is prefill, quadratic-ish, ~190s at 30k tokens. Budget by
occupancy, not by window size.

It does not license "long context is free for reasoning". The task sits at the end of the
prompt, the filler is semantically unrelated, n=20, one model, one family, one depth. The
accuracy rise is unexplained and under-powered. The middle-position variant — where the
literature expects the damage — was deliberately not bought by this design.

## Files

- `run.py` — `uv run experiments/012-context-length/run.py run`, then `... report`
- `results/012_context.jsonl` — one record per call, with `num_ctx`, measured `tokens_in`,
  and the prefill/decode/load split now recorded by `_lab.timings()`
