# Deliberation tracks the fraction of peers that are correct, not how many

**2026-09-11, from 009, correcting 008.** qwen2.5 at B1n, n=139 tasks, peers are qwen's own
scored draws so family, prompt, weights and temperature match the subject and only peer
composition moves. Subject's round-one answer is the same draw in every condition.

## What 008 got wrong, and why

008 decomposed its five conditions by **k**, the number of correct peers, found per-k deltas
that were identical across conditions (0 → −0.448, 1 → −0.011, 2 → +0.202), and reproduced
every aggregate from P(k) alone. All of that is still true. But every one of those conditions
used **two** peers, where k and the fraction correct are the same variable up to scaling —
so the decomposition could not tell them apart, and I read it as a count.

009 ran three peers and the count model broke exactly where the two variables separate:

| k | n | 009 (3 peers) | 008 (2 peers) | diff |
|---|---|---|---|---|
| 0 | 50 | −0.460 | −0.448 | −0.012 |
| 1 | 234 | **−0.132** | **−0.011** | **−0.121** |
| 2 | 94 | +0.160 | +0.202 | −0.042 |

k=0 and k=2 transfer. k=1 misses by 0.121 on n=234, which is not noise. One correct peer is a
*tie* in a two-peer block and a 1-against-2 *minority* in a three-peer one.

## The curve both experiments lie on

| fraction correct | block | n | delta |
|---|---|---|---|
| 0.00 | 2 peers | 183 | −0.448 |
| 0.00 | 3 peers | 50 | −0.460 |
| 0.33 | 3 peers | 234 | −0.132 |
| 0.50 | 2 peers | 185 | −0.011 |
| 0.67 | 3 peers | 94 | +0.160 |
| 1.00 | 2 peers | 327 | +0.202 |
| 1.00 | 3 peers | 39 | +0.128 |

Monotone, and the two block sizes agree wherever they overlap — at 0.00 (−0.448 vs −0.460)
and at 1.00 (+0.202 vs +0.128, n=39, inside noise).

**Leave-one-condition-out, this curve predicts all eight conditions across 008 and 009 with a
maximum residual of 0.034 and a mean of 0.023**, every one inside the 0.050 noise floor, with
no condition contributing to its own prediction. The count model's residuals on 009 reach
0.111.

## What this changes

- **"One correct peer is enough" is false.** It was enough in 008 only because one of two is
  half. One of three is −0.132 — harmful, not neutral.
- **"The composition statistic is max(member accuracy), not mean" is false.** 009 held max
  fixed at 1.00 and moved mean peer accuracy from 0.33 to 0.67: **+0.209**, exact McNemar
  discordant 15/44, **p=0.0002**. A guaranteed-correct member does not saturate the benefit.
- **The deployable rule is a proportion, not a member.** To keep deliberation from hurting,
  most of the block has to be right — the curve crosses zero near fraction 0.5. Adding a
  strong member to a weak panel helps only insofar as it moves that proportion, which means
  it helps *less* the larger the panel. That is the opposite of what 008's note implied.
- **The Condorcet framing 003 and 005 used is closer to right than 008 made it look.**
  Majority voting asks whether the mean member clears a threshold; this says deliberation
  asks roughly whether the correct answer holds a majority of the block. Both are statistics
  of the proportion. 008's "max, not mean" was the detour.

## What is not established

- **Composition at matched mean.** 009's U33 vs S33 compared three mediocre peers against one
  perfect and two useless ones at the same nominal mean: +0.086, predicted +0.074, but
  **p=0.126**, and U33's realised peer accuracy came out 0.283 rather than 0.333 (2.2 se low
  on 417 draws), so the two were not actually matched and the drift flatters the result. The
  direction is right and the significance is not there. Untested, not confirmed.
- **Only two block sizes**, 2 and 3, and the fraction grid is coarse — 0, 1/3, 1/2, 2/3, 1.
  A 4- or 5-peer condition would separate "fraction" from "margin (correct minus wrong)",
  which these data cannot: every cell here has the same ordering under both.
- **The 1.00 cell at three peers is n=39** and sits 0.074 below the two-peer estimate. Within
  noise, but it is the weakest point on the curve.
- Standing limits since 001: one model, one task family, depth 4, peers that are weak
  *samples* of a competent model rather than genuinely weaker models.

## Process note

The fraction model was found by looking at the data after H3 failed, so it is post hoc. What
keeps it from being a curve fit is that it was tested leave-one-condition-out across two
experiments and eight conditions, and that 008's five conditions were never able to
distinguish the two candidate variables. It still deserves its own pre-registered test at a
block size neither experiment used.
