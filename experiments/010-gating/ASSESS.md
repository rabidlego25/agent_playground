# 010 — ASSESS

Schema: `experiments/ASSESS-TEMPLATE.md`. Written for a model with no access to this repo.

## 1. Claim

An agent should revise its answer **only when every peer disagrees with it**; that gate is worth
**+0.101 accuracy** over always-deliberating, on two experiments it was not fitted to.

## 2. Status

Complete 2026-09-11. **Zero new model calls, zero cost** — 010 is a re-analysis of traces
already recorded by 001 and 004. n = 1,170 measured instances (195 tasks × 3 agents × 2
experiments).

## 3. Pre-registered

Four hypotheses, committed before the analysis ran:

- **H1** `agree_frac` predicts "most peers are correct" at **AUC ≥ 0.70** on natural blocks.
- **H2** `peers_with_me` predicts peer correctness *better* than `agree_frac`, and is worth
  **≤ +0.01** as a gate. (Informative ≠ actionable.)
- **H3** some gate beats always-deliberate by **≥ +0.03** out of sample, threshold fitted on
  one experiment and evaluated on the other.
- **H4** the same features on 008's and 009's *selected* blocks give **AUC ≤ 0.60**.

Features were restricted in advance to quantities an agent can compute at runtime — peer
answers and its own round-one answer, never correctness.

**Post hoc, and flagged as such:** the winning gate is `peers_with_me == 0`. The pre-registered
search tested only `feature ≥ threshold` and returned a degenerate threshold firing on 100%.
The rule was found by reading the cell table afterwards. It is evaluated without fitting on
both experiments, but its *form* was chosen after seeing the data.

## 4. Method

- **Model:** qwen2.5 (7B, local via ollama), three agents per block, one family.
- **Task:** `multi_hop` depth 4, n=195 per experiment.
- **Design:** round one answers exchanged, then revision. Peers of an agent = the other two
  agents' round-one answers, scored against stored gold.
- **Natural vs selected blocks** is the central methodological move. 008/009 *selected* peers
  to hit an accuracy target, destroying within-task correlation. 010 uses blocks as they fell.
- **Statistic:** AUC for prediction; mean per-instance delta (±1 per instance) for gate value.
  Run-to-run noise floor 0.050, task-set variance 0.163.

## 5. Result

| hypothesis | predicted | observed | verdict |
|---|---|---|---|
| H1 | AUC ≥ 0.70 | **0.934** | confirmed |
| H2 | gate value ≤ +0.01 | **+0.000** | confirmed |
| H3 | ≥ +0.03 out of sample | **+0.101** | confirmed, by a post hoc rule |
| H4 | AUC ≤ 0.60 on selected | **0.810** | **refuted** |

Gate value, against always-deliberate at −0.040: fires on **28%** of instances, worth
**+0.061** absolute, **+0.101** relative. Held out separately: **+0.108** (001), **+0.095** (004).

Mechanism: deliberation is worth **+0.481** when the subject is already wrong (n=376) and
**−0.287** when it is already right (n=794). So the only question at runtime is *am I wrong*,
and peer disagreement answers it: P(wrong | every peer disagrees) = **0.696** against a base
rate of **0.321**; P(wrong | every peer agrees) = **0.032**.

H4's refutation matters more than the confirmations. It kills the stated *rationale* for H1 —
that the signal comes from task-difficulty clustering. The signal survives in blocks where
correctness was assigned independently of the task, so the real mechanism is that **wrong
answers are diverse and right answers concentrate**: a property of the answer space, not of
task clustering. The prediction was right for the wrong reason.

## 6. Threats

- **The rule's form is post hoc.** Needs one pre-registered confirmation on data neither 001
  nor 004 supplied. Both evaluations here are unfitted, which is weaker than pre-registered.
- **Two peers, one model, one task family, depth 4.** At five peers the useful cut may be a
  proportion rather than unanimity. Untested.
- **Gate assumes peers already exist.** It answers when to *revise*, not whether to pay for a
  panel. The +0.101 does not net out the cost of the peers it conditions on.
- **`peers unanimous` at +0.026 does not clear the 0.050 run-to-run floor** and should not be
  read as a real effect. The headline +0.101 does clear it.
- **Single model family.** qwen2.5 measured at 0.51 solo on this task; whether the diversity-of-
  wrong-answers mechanism holds for a stronger model is untested and is the obvious next arm.

## 7. Artifacts

- `experiments/010-gating/run.py` — the full re-analysis, deterministic, no model calls.
- `results/001_deliberate*.jsonl`, `results/004_deliberate*.jsonl` — source traces.
- `results/004_samples*.jsonl` — the draw-level data behind the clustering argument.
- `tests/_lab.py` — `wilson()`, `mcnemar()`; the intervals and paired test used here.

## 8. Challenge

1. The rule is post hoc in form but unfitted in evaluation. Is "+0.101 on two held-out
   experiments" a defensible headline, or should it be reported as a hypothesis for 012?
2. H4 was refuted and the mechanism rewritten to fit. Is "wrong answers are diverse" a real
   explanation, or a second story fitted to a second observation with no new prediction?
3. Deliberation is *negative* overall (−0.040). Is a gate that recovers value from a
   net-harmful intervention a useful result, or evidence the intervention should be dropped?
4. n=1,170 is instance-level but comes from 195 tasks × 2 experiments. Are the effective
   degrees of freedom closer to 390? If so, which intervals here are overstated?
5. The subject-wrong split (+0.481 vs −0.287) is conditioning on an outcome. Does that
   introduce selection bias into the mechanism story, even though the gate itself never
   observes correctness?
