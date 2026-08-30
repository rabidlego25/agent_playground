# 003 — Does a mixed-family panel restore what deliberation destroys?

**Status:** running (2026-08-30). **Hypotheses stated before any arm was run.**

## Question

001 found deliberation costs 1.85× a non-communicating control for identical accuracy
(0.610 either way; 500,045 tokens vs 269,982), and proposed a mechanism rather than
stopping at the null: agents move together, so discussion spends the error independence
that majority voting depends on. Evidence was that individual agents got *better* —
129 wrong→right against 93 right→wrong, net +36 corrections across 585 slots — while the
vote captured none of it, and unanimity rose 0.30 → 0.48 with reliability flat at 0.78.

That explanation makes a falsifiable prediction. Three instances of one model share
weights, so a peer answer carries a strong prior and little new information. Three
different *families* do not have that shortcut. If correlation is the problem, varying
family should shrink it.

**This experiment exists to be able to prove 001's explanation wrong.**

## Hypotheses

- **H1.** A mixed-family vote beats the best single family in it, at k=3. (Heterogeneous
  ensembling works — the standard result, included because a failure here means the panel
  is too unequal in capability for any of the rest to be interpretable.)
- **H2 (the question).** The deliberation penalty is smaller for a mixed panel than for a
  single-family panel. Operationally: `D-mixed − C-mixed` exceeds `D-homo − C-homo`
  (= 0.610 − 0.585 = +0.025, p=0.50) by enough to matter, at matched token cost.
  **Predicted to hold, weakly.** This is the reverse of 001's pre-registration and it is
  deliberately the softer prediction: heterogeneity should reduce herding, but the task
  still has no division of labour, so there is still nothing for agents to trade.
- **H3.** Cross-family agreement rises less under deliberation than within-family
  agreement did (0.30 → 0.48). If the mind-change rate stays near 50% while unanimity
  rises less, agents are moving *without* converging — information-following rather than
  herding, which is the distinction 001 could not make.

## Design

n=195, `multi_hop` depth 4, temperature 0.7 — identical task instances and seeds to 001
(5000–5194), so every arm here is paired against every arm there.

Panel: `qwen2.5` 7B (Alibaba), `llama3.1` 8B (Meta), `mistral:7b` (Mistral). **Size-matched
at 7–8B so family varies and capacity does not** — a 9B third member would confound the
two. The revision prompt is byte-identical to 001's; the peers differ, the wording must not.

qwen2.5's round-one sample is **reused from 001** rather than redrawn: same weights, same
task, same seed, so the draw is identical and the two experiments share sampling noise
instead of each paying for its own.

Phases run one model at a time rather than one task at a time. A 16 GB machine holds two
7–8B models comfortably and three not at all, so per-task interleaving would thrash on
model load; one pass per model is one load per model.

## What counts as an answer

H2 is a **difference of differences**, and the honest version reports it as such: the
single-family gap is +0.025 with p=0.50, i.e. indistinguishable from zero, so "mixed does
better than that" is a low bar and clearing it narrowly means nothing. The result is
interesting only if `D-mixed` clears `C-mixed` on a paired McNemar in its own right.

Cost normalisation is unchanged from 001: D pays for the round-one samples it reuses.

## Known weaknesses

- Three families is n=3 on the blocking factor. If mistral is much weaker than the other
  two the vote degenerates toward the stronger pair and H2 is untestable — H1 is the guard
  against reporting that case as a result.
- Same single task family as 001. A lookup task may be the worst case for deliberation
  regardless of who is deliberating; that confound is not addressed here and needs a task
  with separable subgoals.
- Position in the peer list is held fixed per family (A/B/C follows panel order), which
  keeps family from being confounded with position but means position effects are not
  measured. Shuffling order is a separate, cheap follow-up.
