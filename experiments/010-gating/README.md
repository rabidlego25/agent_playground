# 010 — Can the deliberation curve be used, or only described?

**Status:** complete 2026-09-11. 1,170 measured instances, **zero new model calls**.
**H1 and H3 confirmed, H2 confirmed, H4 refuted. The curve is usable, and the usable
observable is not the one 008/009 pointed at.**

> **Deliberate only when your peers disagree with you.** Always-deliberate is worth
> **−0.040**. Gating on "every peer disagrees with me" is worth **+0.061**, a gain of
> **+0.101**, firing on 28% of instances. Held out across the two experiments separately:
> **+0.108** (001) and **+0.095** (004). Both prompts, neither fitted.

## Result

**H1 confirmed, by a wide margin.** Peer agreement predicts peer correctness at **AUC 0.934**
on natural blocks, against a predicted ≥0.70.

| feature | AUC natural | AUC selected |
|---|---|---|
| `agree_frac` | **0.934** | 0.810 |
| `unanimous` | 0.934 | 0.766 |
| `consensus_with_me` | 0.882 | 0.729 |
| `peers_with_me` | 0.816 | 0.688 |

**H4 refuted.** Selected blocks predict at 0.810, not the ≤0.60 predicted. Selection does not
destroy the signal, so the rationale behind H1 — that the signal comes from task-difficulty
clustering — is wrong. It survives in blocks where correctness was assigned independently of
the task, which means agreement predicts correctness because **wrong answers are diverse and
right answers concentrate**, a property of the answer space rather than of task clustering.

**H2 confirmed.** `peers_with_me` predicts correctness well (0.816) and is worth **+0.000**
as a gate, exactly as predicted: when peers already agree with you, revision has nothing to
change. Predicting peer correctness and knowing when to act are different problems.

**H3 confirmed at +0.10, not the +0.03 threshold** — but by a rule the pre-registered search
did not find. That search only tested `feature ≥ threshold`; the useful gate on
`peers_with_me` is `== 0`, in the other direction, so the automated sweep returned a
degenerate threshold firing on 100%. The rule came from reading the cell table:

| gate | fires | value | vs always |
|---|---|---|---|
| always deliberate | 1.00 | −0.040 | — |
| peers unanimous | 0.55 | −0.014 | +0.026 |
| any peer disagrees with me | 0.60 | +0.023 | +0.063 |
| **every peer disagrees with me** | **0.28** | **+0.061** | **+0.101** |

## Why it works, and what it says about 008/009

Splitting by whether the subject was already right explains everything:

| subject round one | n | delta |
|---|---|---|
| already right | 794 | **−0.287** |
| already wrong | 376 | **+0.481** |

Deliberation is enormously valuable when you are wrong and purely destructive when you are
right, where it is capped at 0 by construction and averages −0.287. So the only question that
matters at runtime is *am I wrong*, and peer disagreement answers it almost perfectly:

- P(subject wrong | every peer disagrees) = **0.696**, against a base rate of 0.321
- P(subject wrong | every peer agrees) = **0.032**

**This reframes 008 and 009.** Both held the subject's round-one answer fixed and selected
peers independently of it, so they measured the causal effect of peer composition with the
subject's own correctness averaged out at 0.647. That curve is real. But in deployment peer
correctness and subject correctness are correlated — same model, same task — so the
fraction-correct curve is substantially a *proxy* for "is the subject wrong". The 008/009
curve still operates within each regime (given the subject is wrong, delta rises 0.353 →
0.402 → 0.669 with peer fraction), it is simply not the variable a deployed agent should
condition on.

## What is not established

- **The rule was found by inspection after the pre-registered search failed**, so its
  threshold-free form is post hoc even though both experiments evaluate it without fitting.
  It needs one pre-registered confirmation on data neither 001 nor 004 supplied.
- **Two peers, one model, one task family, depth 4.** Whether "every peer disagrees" stays
  the right cut at larger block sizes is untested — at five peers the useful cut may be a
  proportion rather than unanimity.
- **The gate costs nothing to evaluate but assumes peers already exist.** It answers when to
  *revise*, not whether to pay for a panel at all.
- The delta per instance is ±1, and the 0.050 run-to-run floor applies; the +0.101 gain
  clears it, the +0.026 for `peers unanimous` does not.

## Question

008 and 009 established that the revision delta tracks the **fraction of peers that are
correct**: ≈ −0.45 at fraction 0, crossing zero near 0.5, ≈ +0.20 at 1. That is a rule about
a quantity nobody can observe at runtime — if you knew which peers were right you would not
be deliberating.

So the curve is only useful if some **observable** predicts that fraction. If none does, 008
and 009 describe a curve nobody can act on, and that is worth writing down plainly.

## Why this is answerable without new calls

`001_deliberate` and `004_deliberate` each ran three qwen2.5 agents that exchanged round-one
answers and revised. For any agent, its **peers are the other two agents' round-one
answers** — recorded in the traces — and peer correctness is recoverable by scoring those
answers against the stored gold. That is **1,170 measured instances on natural blocks**
(195 tasks × 3 agents × 2 experiments), with the real revision outcome for each.

Natural blocks matter here. 008 and 009 *selected* peers to hit an accuracy target, which
destroys the within-task correlation a deployment would actually see: in `004_samples`, 50 of
195 tasks have all six draws correct and only 6 have none, so peer correctness is strongly
clustered by task. Selection removes exactly the structure a gate would exploit.

## Features, all computable by an agent at runtime

From the peer answers and its own round-one answer only — never from correctness:

- `agree_frac` — share of peers giving the modal peer answer
- `n_distinct` — distinct peer answers / number of peers
- `peers_with_me` — share of peers matching the agent's own round-one answer
- `unanimous` — all peers agree with each other
- `consensus_with_me` — all peers agree *and* they agree with the agent

## Predictions, committed before running

- **H1 (predictability).** On natural blocks, `agree_frac` predicts "most peers are correct"
  with **AUC ≥ 0.70**. Rationale: peer correctness is clustered by task difficulty, and on
  easy tasks draws concentrate on the right answer.
- **H2 (the trap).** `peers_with_me` will predict peer correctness *better* than
  `agree_frac` — and be worth little as a gate, because when peers already agree with the
  agent, revision has almost nothing to change. Predicted gate value **≤ +0.01**. The
  informative case and the actionable case are not the same case.
- **H3 (the decision).** Some gate beats always-deliberate by **≥ +0.03** out of sample,
  with the threshold fitted on one experiment and evaluated on the other. Below +0.03 the
  honest conclusion is that the curve is descriptive.
- **H4 (why 008/009 could not have shown this).** The same features on 008's and 009's
  *selected* blocks give materially lower AUC — **≤ 0.60** — because selection breaks the
  task-difficulty clustering. If H4 fails and selected blocks predict just as well, then the
  signal is not coming from difficulty clustering and H1's rationale is wrong.

**What would falsify the enterprise:** every feature at AUC ≤ 0.60 on natural blocks. Then
the fraction is unobservable, the gate is impossible, and 008/009 are a description.

## Known weaknesses, stated in advance

- **One model, one task family, depth 4**, and blocks of exactly two peers. The standing
  limitation since 001.
- **001 and 004 used different prompts** (bare vs B1n), which is what makes the
  cross-experiment threshold transfer a real test rather than a re-fit — but it also means a
  gate that fails to transfer may be failing on prompt, not on principle.
- **A gate that fires rarely is cheap to over-fit.** Fire rate is reported alongside every
  gate value, and a gate firing on under 10% of instances is not counted as a result.
- The measured delta per instance is ±1, so gate values carry the same 0.050 run-to-run
  noise floor as everything else in this repo.
