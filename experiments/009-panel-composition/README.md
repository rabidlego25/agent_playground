# 009 — Is deliberation harm set by P(no correct peer), or by mean peer competence?

**Status:** complete 2026-09-11. n=139 per condition, 417 local calls, no API cost.
**H2 confirmed, H1 not established, H3 refuted — and the refutation is the finding.**

| condition | peers | mean | max | realised mean | P(k=0) | delta | 95% CI |
|---|---|---|---|---|---|---|---|
| U33 | (0.33, 0.33, 0.33) | 0.333 | 0.33 | **0.283** | 0.360 | **−0.209** | [0.359, 0.522] |
| S33 | (1.00, 0.00, 0.00) | 0.333 | 1.00 | 0.333 | 0.000 | −0.122 | [0.443, 0.606] |
| S67 | (1.00, 0.50, 0.50) | 0.667 | 1.00 | 0.676 | 0.000 | **+0.086** | [0.655, 0.800] |

- **H2 confirmed, and it refutes the claim this experiment was built to check.**
  S67 − S33 = **+0.209** at identical max (1.00), exact McNemar discordant 15/44,
  **p=0.0002**. Adding competent members beyond the first is worth 0.209. **Max is not the
  composition statistic**, and 008's note was wrong to say so.
- **H1 not established.** S33 − U33 = +0.086 against a predicted +0.074, but McNemar is
  20/32, **p=0.126**. Worse, **U33's realised peer accuracy came out 0.283, not 0.333** —
  2.2 standard errors low on 417 Bernoulli draws — so the two conditions are not matched on
  mean after all, and the drift runs in the direction that flatters H1. Conditioning on the
  realised draws instead, composition alone predicts +0.119 where +0.086 was observed. The
  effect is in the predicted direction and does not clear significance. Stated as unproven.
- **H3 refuted.** 008's per-k constants do not transfer to three-peer blocks:

  | k | n | 009 | 008 | diff |
  |---|---|---|---|---|
  | 0 | 50 | −0.460 | −0.448 | −0.012 |
  | 1 | 234 | **−0.132** | **−0.011** | **−0.121** |
  | 2 | 94 | +0.160 | +0.202 | −0.042 |
  | 3 | 39 | +0.128 | — | (008 never observed it) |

> **What replaces it: the delta tracks the *fraction* of peers that are correct, not the
> count.** k=1 means a tie in a two-peer block and a 1-against-2 minority in a three-peer
> one, which is why the count model breaks and the fraction model does not. Sorted by
> fraction, the two experiments interleave into one monotone curve — 0.00 → −0.45, 0.33 →
> −0.13, 0.50 → −0.01, 0.67 → +0.16, 1.00 → +0.19 — with the two block sizes agreeing at
> both ends where they overlap. Leave-one-condition-out, that curve predicts all **eight**
> conditions across 008 and 009 with a **max residual of 0.034** (mean 0.023), no condition
> contributing to its own prediction. The count model missed by up to 0.111.
>
> **"One correct peer is enough" is false.** One correct peer out of three is −0.132. It was
> enough in 008 only because one of two is half of them.

## Question

008 found that qwen's delta depends on **k**, the number of correct peers in the block, and
not on the competence gap: per-k deltas were identical across five conditions (k=0 −0.448,
k=1 −0.011, k=2 +0.202) and only the mixture moved. Feeding each condition's P(k) through
those three constants reproduced its aggregate delta to within 0.022.

The note written from it (`notes/2026-09-11-one-correct-peer-is-enough.md`) claimed this
makes the composition statistic **max(member accuracy), not mean**, and that a 1-strong /
2-weak panel should be safe where three mediocre members are not. That was an inference from
a model fitted entirely on **two i.i.d. peers**. Nothing in 008 varied block size or
composition, so the claim is untested.

This tests it, and it can fail in two distinguishable ways.

## Design

Same machinery as 008 — peers are qwen2.5's own scored draws from `004_samples.jsonl`, same
139 tasks, subject's round-one answer is draw 0 and is never re-run, so conditions pair
exactly on task. **Three peers** rather than two: composition cannot vary with two.

| condition | peer accuracies | mean | max | P(k=0) |
|---|---|---|---|---|
| **U33** | (0.33, 0.33, 0.33) | 0.333 | 0.33 | 0.296 |
| **S33** | (1.00, 0.00, 0.00) | 0.333 | 1.00 | 0.000 |
| **S67** | (1.00, 0.50, 0.50) | 0.667 | 1.00 | 0.000 |

The two comparisons cut in opposite directions, which is the point:

- **U33 vs S33 — same mean, different max.** If mean competence is what matters these are
  the same panel. If P(no correct peer) is what matters they are not.
- **S33 vs S67 — same max, different mean.** If "one correct peer is enough" is literally a
  threshold, these are the same. If the response keeps climbing above k=1, they are not.

**Peer order is shuffled within every block.** S33's strong member is otherwise always
Assistant A, and a positional regularity the subject could learn would confound the whole
comparison. 008 did not need this because its peers were i.i.d.

417 revision calls, local `ollama`, ~55 min at the 7.9 s/call measured in 005. No API quota,
no money.

## Predictions, committed before the run

Using 008's pooled per-k constants (−0.448 / −0.011 / +0.202, with k=3 assumed to behave as
k=2 since 008 never observed it):

| condition | predicted delta |
|---|---|
| U33 | −0.085 |
| S33 | −0.011 |
| S67 | +0.149 |

- **H1 (P(k=0) is the mechanism).** S33 − U33 = **+0.074**, and the sign is positive. At
  matched mean, replacing three mediocre peers with one perfect and two useless ones *helps*.
  - If the observed gap is **≥ +0.05** (the run-to-run noise floor), P(no correct peer) is
    the mechanism and the composition advice in 008's note stands.
  - If it is **≈ 0**, mean competence is what matters after all, 008's k-model is a
    coincidence of its uniform design, and **that note's closing claim is wrong.**
- **H2 (it is not a pure threshold).** S67 − S33 = **+0.160**, well clear of the floor. If
  this comes out ≈ 0, the response saturates at one correct peer and "one correct peer is
  enough" is literally true rather than approximately true — a stronger and cleaner claim
  than 008 made, and it would mean adding competent members beyond the first buys nothing.
- **H3 (the constants transfer out of sample).** The per-k deltas measured here at k=0..3
  match 008's within the noise floor, and each condition's aggregate is reproduced by its
  own observed P(k) times 008's constants, residual ≤ 0.05. This is the load-bearing test:
  008 fitted those constants on two i.i.d. peers, and this applies them to three
  heterogeneous ones. If H3 fails while H1 holds, the step is real but block-size-dependent.

**What would falsify the whole framing:** U33 ≈ S33 ≈ S67. That would mean none of k, mean
or max predicts the delta at fixed subject, and the 008 decomposition does not generalise
past its own design.

## Known weaknesses, stated in advance

- **Peer accuracy 0.00 and 1.00 are achieved by selection**, so S33's weak members are
  always wrong and its strong member always right. Real panels are not deterministic. This
  is the sharpest available contrast, not a realistic panel, and the point is the mechanism.
- **Same limitation as 008:** one model, one task family, depth 4, peers that are weak
  *samples* of a competent model rather than genuinely weaker models.
- **k=3 has no 008 prior.** Treating it as k=2 is an assumption, flagged here rather than
  discovered afterwards.
- **The 139-task set** excludes tasks qwen always or never gets right, so it is harder than
  the full pool (solo 0.647 vs 0.692) and magnitudes do not transfer to it.
- **n=139, one run per condition**, against a 0.050 run-to-run noise floor. H1's predicted
  +0.074 clears that, but not by much; H2's +0.160 does comfortably.
