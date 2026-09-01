# 004 — Does the ensembling gain survive at the top of the prompt axis?

**Status:** samples phase complete (2026-09-01); arm D′ running.
**Hypotheses were pre-registered and committed (9865633) before any arm was run.**
**Result: H1 confirmed — 001's ensembling finding survives the prompt fix. H2 and H3
both rejected: the gain grew rather than shrank, because the reasoning prompt made
errors *more* independent, not less.**

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

## Results — samples phase (2026-09-01, n=195)

**H1 confirmed. H2 rejected. H3's correlation account rejected.** Both pre-registered
predictions were wrong, and wrong in the same direction: the two axes compose instead of
competing.

| arm | acc | 95% CI | tok_in | tok_out | total |
|---|---|---|---|---|---|
| A: single sample, bare | 0.51 | [0.44, 0.58] | 31,838 | 21,976 | 53,814 |
| C: k=3 vote, bare | 0.58 | [0.51, 0.65] | 95,514 | 66,683 | 162,197 |
| C: k=5 vote, bare | 0.61 | [0.54, 0.68] | 159,190 | 110,792 | 269,982 |
| C: k=7 vote, bare | 0.63 | [0.56, 0.69] | 222,866 | 153,290 | 376,156 |
| A′: single sample, B1n | 0.67 | [0.60, 0.73] | 37,688 | 18,021 | 55,709 |
| C′: k=3 vote, B1n | 0.74 | [0.67, 0.80] | 113,064 | 53,185 | 166,249 |
| C′: k=5 vote, B1n | 0.83 | [0.77, 0.88] | 188,440 | 87,572 | 276,012 |
| **C′: k=7 vote, B1n** | **0.86** | [0.81, 0.90] | 263,816 | 122,555 | 386,371 |

Paired exact McNemar, all arms on the same 195 instances:

| contrast | acc | 1st only | 2nd only | p |
|---|---|---|---|---|
| A′ vs C′3 | 0.67 → 0.74 | 6 | 20 | **0.0094** |
| A′ vs C′5 | 0.67 → 0.83 | 2 | 34 | **<0.0001** |
| A′ vs C′7 | 0.67 → 0.86 | 2 | 40 | **<0.0001** |
| A bare vs A′ | 0.51 → 0.67 | 28 | 58 | **0.0016** |
| C3 vs C′3 | 0.58 → 0.74 | 24 | 54 | **0.0009** |
| C5 vs C′5 | 0.61 → 0.83 | 12 | 55 | **<0.0001** |
| C7 vs C′7 | 0.63 → 0.86 | 10 | 56 | **<0.0001** |

### H1 — confirmed

Voting still beats a single sample on the reasoning prompt, at every k (p=0.0094 at k=3,
p<0.0001 at k=5 and 7). **001's H1 is a result about ensembling, not an artifact of a weak
prompt.** That was the question this experiment was built to answer.

### H2 — rejected. The gain did not shrink; above k=3 it grew

| k | gain bare | gain B1n | delta |
|---|---|---|---|
| 3 | +0.072 | +0.072 | +0.000 |
| 5 | +0.097 | +0.164 | **+0.067** |
| 7 | +0.113 | +0.195 | **+0.082** |

Identical at k=3 to three decimal places, and *larger* at k=5 and k=7 — both deltas above the
0.050 run-to-run variance floor. This is a difference of differences read against the noise
floor as pre-registered, not a formal test, and it is the weakest-supported claim on this page.
But the direction is unambiguous and it is the opposite of the prediction.

The standard intuition behind H2 — less headroom, so less to gain — is simply not what
happened. Returns also stopped saturating: on the bare prompt no adjacent-k step above 3 was
significant, so 001 concluded ensembling saturates at k=3. On the reasoning prompt k=5 and k=7
keep paying (0.74 → 0.83 → 0.86). **Where the ensembling curve saturates is a property of the
prompt, not of the ensemble.**

### H3 — the correlation account predicted the wrong sign

| prompt | c = P(second draw repeats the first's answer \| first is wrong) | ordered pairs |
|---|---|---|
| bare | **0.339** | 3,912 |
| B1n | **0.239** | 2,520 |

Errors became *more* independent, not less. Asking the model to reason did not channel every
sample down one derivation; it removed a class of correlated error — the shared wrong attractor
that three bare-prompt samples fall into together — and left behind residual errors that are
closer to independent.

That is why H2 failed, and the two results are one result: **ensembling gains rose because the
prompt bought back the error independence that a majority vote spends.** Base rate and error
independence are separate quantities, and a good prompt moves both in the direction voting
wants.

This does not overturn 001's or 003's correlation findings — it bounds them. Deliberation (001
arm D), in-context repetition (001 B3n, −0.22), and unequal mixed panels (003) all *spend*
error independence. A reasoning prompt *buys* it. The mechanism is the same axis; the
interventions sit on opposite ends of it.

### Consensus became a better signal, on both coverage and reliability

| distinct answers among 3 | bare: tasks | bare: majority correct | B1n: tasks | B1n: majority correct |
|---|---|---|---|---|
| 1 (unanimous) | 58 | 0.78 | **97** | **0.90** |
| 2 | 109 | 0.57 | 76 | 0.68 |
| 3 | 28 | 0.25 | 22 | 0.23 |

Unanimity coverage rose 0.30 → 0.50 **and** its reliability rose 0.78 → 0.90. This is the exact
contrast to 001's H3, where deliberation raised coverage 0.30 → 0.48 with reliability flat at
0.78 — more cases labelled confident at no better than the old base rate, i.e. a strictly worse
signal. Same coverage increase, opposite value. Prompting and deliberation both make a panel
agree more; only one of them makes agreement mean more.

### The practitioner answer, at matched cost

001 concluded the k=7 vote was not worth 7× a single sample for +0.11. At effectively the same
token spend the reasoning prompt changes what that money buys:

| | tokens | acc |
|---|---|---|
| C7, bare prompt | 376,156 | 0.63 |
| C′7, B1n prompt | 386,371 | **0.86** |

**+0.23 for +2.7% tokens.** And the cheapest arm here (A′, 55,709 tokens, 0.67) still beats the
most expensive bare-prompt arm (C7, 376,156 tokens, 0.63) — 001's headline finding survives
intact. The ordering to draw from both experiments: fix the prompt first, because it is free and
it raises the ceiling everything else operates under; *then* ensemble, because ensembling works
better after it.

### Run-to-run replicate on the headline number

A′ (0.67, seed block +300) against 001's B1n arm (0.718, seed block +203) — same prompt, same
model, same 195 tasks, different draws. **Δ=0.046, at the 0.050 calibration variance floor.**
The pre-registration said this replicate came free with the seed-block choice; it is reported
because a single measurement of 0.72 would have overstated the single-sample rate by about one
noise unit. Neither figure is the "true" B1n rate; the interval is roughly 0.67–0.72.

### Status of H4

Arm D′ (deliberation on the reasoning prompt) is running. Not reported here.
