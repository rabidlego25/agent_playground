# Deliberate only when your peers disagree with you

**2026-09-11, from 010.** No new model calls: 1,170 measured instances recovered from
`001_deliberate` and `004_deliberate`, where three qwen2.5 agents exchanged round-one answers
and revised. For any agent its peers are the other two agents' round-one answers, and peer
correctness scores against the stored gold.

## The rule

| gate | fires | value |
|---|---|---|
| always deliberate | 1.00 | **−0.040** |
| any peer disagrees with me | 0.60 | +0.023 |
| **every peer disagrees with me** | **0.28** | **+0.061** |

A gain of **+0.101** over always-deliberate. Evaluated separately on the two experiments,
which used different prompts (001 bare, 004 B1n) and fitted nothing: **+0.108** and
**+0.095**.

## Why

Split by whether the agent was already right:

| subject round one | n | delta |
|---|---|---|
| already right | 794 | **−0.287** |
| already wrong | 376 | **+0.481** |

Deliberation is worth half a point when you are wrong and destroys a quarter of a point when
you are right, where it is capped at zero and can only take a correct answer away. The whole
decision is therefore *am I wrong*, and peer disagreement answers that almost perfectly:

- P(wrong | every peer disagrees) = **0.696**, base rate 0.321
- P(wrong | every peer agrees) = **0.032**

If your peers agree with you, you are wrong three times in a hundred. There is nothing to
gain and a quarter-point to lose.

## What it does to 008 and 009

008 and 009 held the subject's round-one answer fixed and selected peers independently of it,
so they measured the causal effect of peer composition with subject correctness averaged out
at 0.647. That curve is real and still operates inside each regime — given the subject is
wrong, delta rises 0.353 → 0.402 → 0.669 as the fraction of correct peers goes 0 → 0.5 → 1.

But peers and subject are the same model on the same task, so in any real panel their
correctness is correlated, and **the fraction-correct curve is substantially a proxy for "is
the subject wrong"**. It is the right variable for understanding the mechanism and the wrong
one for conditioning a deployed agent, because it is unobservable while disagreement is free.

## Two things I predicted wrong

- **Peer agreement predicts peer correctness at AUC 0.934**, against a pre-registered ≥0.70.
- **Selection does not destroy that signal** — 0.810 on 008/009's selected blocks against a
  predicted ≤0.60. So the mechanism is not task-difficulty clustering, which selection
  removes. It survives because **wrong answers are diverse and right answers concentrate**: a
  property of the answer space, not of the task distribution. That also predicts the signal
  weakens on tasks with few plausible wrong answers, which is testable and untested.

## Weaknesses

- The rule was found by reading a cell table after the pre-registered threshold search
  returned a degenerate gate — that search only tested `feature ≥ threshold` and the useful
  cut is `peers_with_me == 0`. Both experiments evaluate it without fitting, but its
  discovery was post hoc and it deserves one pre-registered confirmation.
- Two peers, one model, one task family, depth 4. At larger blocks the right cut is probably
  a proportion rather than unanimity, and that is untested.
- It says when to *revise*, not whether to pay for a panel in the first place.
- Everything here is the same 195-task multi_hop pool the repo has used since 001.
