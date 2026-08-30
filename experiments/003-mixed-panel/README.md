# 003 — Does a mixed-family panel restore what deliberation destroys?

**Status:** complete (2026-08-30). **Hypotheses stated before any arm was run.**
**Result: H1 failed — the panel is too unequal to test H2 as designed. The finding that
survives is per-member and was not what the experiment was built to measure.**

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

## Results (2026-08-30, n=195)

| arm | acc | 95% CI | tok_in | tok_out | total |
|---|---|---|---|---|---|
| solo qwen2.5 | 0.51 | [0.44, 0.58] | 31,838 | 21,976 | 53,814 |
| solo llama3.1 | 0.22 | [0.17, 0.28] | 28,133 | 32,955 | 61,088 |
| solo mistral:7b | 0.18 | [0.14, 0.24] | 30,615 | 1,573 | 32,188 |
| C-mixed: k=3 vote, no comms | 0.43 | [0.36, 0.50] | 90,586 | 56,504 | 147,090 |
| D-mixed: k=3 + revision round | 0.50 | [0.43, 0.57] | 343,468 | 166,600 | 510,068 |

Paired (exact McNemar), all arms on identical task instances:

| contrast | acc | first-only | second-only | p |
|---|---|---|---|---|
| qwen solo vs C-mixed | 0.51 → 0.43 | 24 | 8 | **0.0070** |
| C-mixed vs D-mixed | 0.43 → 0.50 | 29 | 42 | 0.154 |
| qwen solo vs D-mixed | 0.51 → 0.50 | 40 | 37 | 0.820 |

### H1 — failed, and significantly

The three-way vote lands **below its best member**, p=0.0070. This is Condorcet's jury
theorem on its failure branch: majority voting improves on its members only when they clear
a competence threshold, and two of three sit far below it. The guard fired exactly as the
pre-registration said it would — **it fired on the wrong member.** The design predicted
mistral as the risk; llama3.1 is the *largest* member of the panel and the second weakest.

**The design error is stated plainly: matching the panel on size (7–8B) matches capacity only
if capability tracks parameter count across families, and it does not.** Competence is the
variable that governs whether a vote helps. Size was a proxy for it and a bad one.

### H2 — direction reverses from 001, but does not reach significance

Deliberation moved the mixed panel 0.43 → 0.50 (p=0.154). In 001's single-family panel
deliberation did nothing (p=0.50); here it recovers most of what heterogeneity broke, which
is the predicted direction. It is not established at this n.

It is also not useful. D-mixed (0.50) is statistically indistinguishable from qwen2.5
**alone** (0.51, p=0.820) at **9.5× the tokens** — 510,068 against 53,814. Deliberation
repaired damage the panel design caused, and the repaired result equals doing nothing.

Because C-mixed is a broken baseline, the pre-registered difference-of-differences against
001 is not computed. Comparing a treatment to a control that is worse than its own best
component measures the control's defect, not the treatment.

### The result that survives: deliberation transferred capability, it did not average

| member | pre → post | changed answer | of those, adopted a peer's answer |
|---|---|---|---|
| qwen2.5 (strong) | 0.51 → 0.50 | 57% | 59% |
| llama3.1 (weak) | 0.22 → 0.19 | 79% | 35% |
| **mistral:7b (weak)** | **0.18 → 0.31** | 82% | 56% |

The strong member was **not dragged down**. It revised 57% of its answers and finished where
it started. Mistral gained +0.13 — most of the way from its own level toward qwen's — for the
cost of reading two peer answers.

This is capability transfer, not regression to the mean, and it is the opposite of what a
herding account predicts. The vote could not cash it because the panel was still two weak
members against one strong one. **A composition where the strong side is not outvoted should
capture it**, and that is the cheap follow-up: a two-member panel, or a weighted vote.

Note the asymmetry between the two weak members: mistral adopted a peer answer in 56% of its
revisions and gained; llama adopted one in 35% and lost 0.03. Being willing to be moved is
what paid, not being weak.

### Consensus means opposite things in different panels

| distinct answers among 3 | 001 single-family | 003 mixed panel |
|---|---|---|
| 1 (unanimous) | **0.78** | **0.31** |
| 2 | 0.57 | 0.36 |
| 3 | 0.25 | 0.56 † |

† **Artifact, not a finding.** With three distinct answers the majority is a three-way tie,
and the tie-break follows panel order, so "all three disagree" is literally "trust qwen2.5"
(41/73 = 0.56, against its 0.51 solo rate). The row measures the tie-break rule. It is left
in the table rather than deleted because deleting it would hide that the rule is load-bearing
wherever members are unequal.

The first row is real and is the useful one. **Unanimity predicted 0.78 correct in a
competent homogeneous panel and 0.31 in an unequal mixed one.** When a mixed panel agrees it
is frequently because two weak members fell into the same wrong attractor. Consensus is a
correctness signal in one composition and a shared-error-mode warning in the other, with no
change to the voting rule — only to who is in the room.

## Follow-ups

- **Capability-matched panel.** The cheap version keeps everything local and lowers task depth
  until all three members clear 0.5, since the threshold is what matters, not the depth. The
  other version drops local models for free-tier API families.
- **A composition where the strong side is not outvoted** — two members, or a vote weighted by
  solo accuracy. The capability-transfer result above is currently unmonetisable and this is
  what would monetise it.
- **Willingness to be moved as a variable.** Mistral gained by adopting peer answers; llama
  lost by resisting them. That is one observation each and worth a designed test.

## Known weaknesses

- ~~Three families is n=3 on the blocking factor. If mistral is much weaker than the other
  two the vote degenerates and H2 is untestable — H1 is the guard against reporting that
  case as a result.~~ **This happened.** H1 failed at p=0.0070 and H2 was not reported as a
  clean result. The prediction was right and named the wrong member: llama3.1, the largest
  model in the panel, was the second weakest.
- Every arm here uses 001's bare prompt, which 001's own arm B later showed is worth 0.21 to
  a single call. All three members were measured well below their prompt ceiling, so their
  solo rates — and therefore the Condorcet threshold question — would look different on a
  reasoning prompt. See `notes/2026-08-30-prompt-dominates-configuration.md`.
- Same single task family as 001. A lookup task may be the worst case for deliberation
  regardless of who is deliberating; that confound is not addressed here and needs a task
  with separable subgoals.
- Position in the peer list is held fixed per family (A/B/C follows panel order), which
  keeps family from being confounded with position but means position effects are not
  measured. Shuffling order is a separate, cheap follow-up.
