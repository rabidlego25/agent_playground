# 004 — Does the ensembling gain survive at the top of the prompt axis?

**Status:** pre-registered 2026-09-01, samples phase running. **No results yet.**

## Question

001 measured its entire configuration curve — single sample 0.51, k=3 vote 0.585, k=7 vote
0.626, deliberation 0.610 — on a prompt that never asks the model to reason. Arm B1n then
added one sentence ("Before answering, work through the reporting chain step by step") and
reached **0.72 for fewer tokens than a single bare sample**. Every configuration effect in 001
fits inside a band a single sentence moves you across.

That leaves 001's H1 result — voting beats a single sample, p=0.0125 — provisional in a
specific way. Ensembling gains generally shrink as the base rate rises, and at 0.72 the
headroom is 0.28 rather than 0.49. If the whole gain is headroom, "ensemble your agents" is
advice that evaporates the moment the prompt is fixed.

**This experiment exists to decide whether 001 is a result about ensembling or a result about
a weak prompt.** It is a re-run of exactly one thing: the prompt.

## Design

Identical to 001's `samples` phase in every respect except the prompt string.

n=195, `multi_hop` depth 4, temperature 0.7, `qwen2.5` 7B, seeds 5000–5194, k_max=7,
max_tokens=800. Same task instances as 001 and 003, so **every arm here is paired against
every arm there** — no marginal-interval comparisons.

The prompt is not retyped. `run.py` loads `B_ONE_N` out of `001-deliberation/run.py` at import
time, so the two arms cannot drift apart silently.

Draw seeds are `seed*10 + 300 + j`, disjoint from 001's samples (`+j`), deliberate (`+100+j`)
and budget (`+200+…`) blocks. The existing B1n arm in `001_budget2.jsonl` is therefore an
*independent replicate* of the k=1 cell rather than one of these draws, which buys a
run-to-run variance estimate on the headline number for free.

As in 001, arm A′ is the k=1 prefix and C′ at any k ≤ 7 is the k-prefix of the same draws:
one sweep yields the whole cost curve and the arms share sampling noise.

## Hypotheses

- **H1.** Voting still beats a single sample at k=3 on the reasoning prompt (paired exact
  McNemar, p<0.05). *Predicted to hold, weakly.*
- **H2 (the question).** The ensembling gain is smaller at the high base rate:
  `(C3′ − A′) < (C3 − A) = +0.072`. *Predicted to hold.* If it fails — if the gain is the
  same or larger — then 001's H1 is a real result about ensembling and survives the prompt
  fix intact.
- **H3 (the mechanism, and the one that discriminates).** Two accounts predict the same sign
  for H2 and different magnitudes:
  - *Headroom only.* Errors stay as independent as they were; the gain shrinks by exactly
    what less room to improve buys.
  - *Correlation.* A reasoning instruction channels every sample down the same derivation, so
    the samples that remain wrong are wrong **together**. The gain shrinks by more than
    headroom explains, and the mechanism is the same one that made 001's arm D fail and 001's
    B3n arm lose 0.22 to B1n.

  Operationalised without a null model, as **conditional-on-wrong agreement** `c`: given two
  draws on the same task and the first is wrong, how often does the second give the *same*
  wrong answer. `c` is computable from both trace sets and is the direct measure of the error
  independence majority voting spends. **Correlation account predicts `c′ > c`.**
  Reported alongside 001's unanimity/reliability table, recomputed on the new draws.

- **H4 (second phase, after `samples`).** Deliberation on the reasoning prompt still fails to
  beat the non-communicating curve at matched tokens, as it did in 001 (1.85× cost, identical
  accuracy). *Predicted to hold.* Runs only after the samples phase lands; it is 585 calls and
  the C′ curve is the pre-registered core.

## What counts as an answer

C′ is a curve of accuracy against total tokens; each contrast is paired exact McNemar against
the 001 arm on the same 195 instances. H2 is a difference of differences, so it is reported
as such and read against the run-to-run variance floor (0.050, `reports/2026-08-30-calibration.pdf`),
not as two overlapping intervals.

The practitioner question this has to answer explicitly: **is there any point on the C′ curve
worth its cost, given B1n alone reaches 0.72 for 51,898 tokens?**

## Known weaknesses, stated in advance

- One prompt at each end of the axis, not a curve along it. "Top of the prompt axis" means
  "best prompt found in three tries", not a ceiling anyone has proved.
- Same single task family as 001 and 003. A lookup task has no division of labour by
  construction; that confound is inherited, not addressed.
- `c` measures agreement between two draws of the *same* model. It cannot separate "the
  reasoning prompt made errors correlated" from "the reasoning prompt fixed exactly the
  uncorrelated errors and left the correlated ones", which predicts the same `c′ > c`.
  Distinguishing those needs the per-task error-type breakdown, which the traces support and
  which is an analysis, not another run.
