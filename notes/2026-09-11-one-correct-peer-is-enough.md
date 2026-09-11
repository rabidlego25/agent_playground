# Deliberation harm is a step function of how many peers are right

**2026-09-11, from 008.** qwen2.5 at B1n, n=139 tasks, peers are qwen's own scored draws so
family, prompt, weights and temperature are identical to the subject and only peer accuracy
moves. The subject's round-one answer is the same draw in every condition, so conditions
pair exactly.

## The curve, and why it is not the finding

| condition | peer accuracy | gap | delta |
|---|---|---|---|
| P100 | 1.00 | +0.35 | **+0.180** |
| P80 | 0.80 | +0.15 | +0.101 |
| P65 | 0.65 | 0.00 | +0.065 |
| P40 | 0.40 | −0.25 | −0.115 |
| P15 | 0.15 | −0.50 | **−0.360** |

Strictly monotone, which was the pre-registered H1. Exact McNemar against the P65 anchor:
P100 discordant 15/31 p=0.026, P40 43/18 p=0.0019, P15 68/9 p<1e−6. P80 does not separate
from P65 (19/24, p=0.54).

H2 said a delta ≤ −0.10 at P15 means harm tracks the competence gap. It does, by a wide
margin, and P40 puts a third point on the same branch at −0.115 — while 005's cross-family
−0.123 at a comparable gap is **2.9× smaller**. Family mismatch is not needed to explain
deliberation harm and shows no sign of adding to it.

H3 said the delta at P100 would be ≥ +0.10. It is +0.180, and that closes something 004
left open. 004 measured net exactly zero at gap 0 and suggested peer answers might simply be
noise to an agent that has already worked the chain. They are not. Given two correct peers
the subject gains 0.18 (38 wrong→right against 13 right→wrong). Deliberation is a capability
channel; it only requires the capability to be in the block.

That is the pre-registered answer, on all five points. The decomposition is the actual finding.

## Bucket by how many peers were right

| k correct | P100 | P80 | P65 | P40 | P15 | pooled |
|---|---|---|---|---|---|---|
| 0 | — | 3, −0.667 | 14, −0.500 | 53, −0.434 | 113, −0.442 | **−0.448** (n=183) |
| 1 | — | 44, +0.023 | 58, −0.034 | 58, +0.000 | 25, −0.040 | **−0.011** (n=185) |
| 2 | 139, +0.180 | 92, +0.163 | 67, +0.269 | 28, +0.250 | 1, +1.000 | **+0.202** (n=327) |

**Within every bucket the delta is the same in every condition.** Peer accuracy changes
nothing about what happens given a peer block; it changes only how often each block occurs.
P(0 correct) runs 0.00 → 0.02 → 0.10 → 0.38 → 0.81 across the five, and that mixture shift is
the entire aggregate effect.

The strong form of that claim is testable and passes. Take the three pooled constants above,
and predict each condition's aggregate delta from its own mixture alone:

| cond | P(0) | P(1) | P(2) | predicted | actual | resid |
|---|---|---|---|---|---|---|
| P100 | 0.00 | 0.00 | 1.00 | +0.202 | +0.180 | −0.022 |
| P80 | 0.02 | 0.32 | 0.66 | +0.120 | +0.101 | −0.020 |
| P65 | 0.10 | 0.42 | 0.48 | +0.048 | +0.065 | +0.017 |
| P40 | 0.38 | 0.42 | 0.20 | −0.135 | −0.115 | +0.020 |
| P15 | 0.81 | 0.18 | 0.01 | −0.365 | −0.360 | +0.005 |

Every residual is inside the 0.050 run-to-run noise floor. A three-parameter model that never
sees the condition reproduces the whole curve. **Peer accuracy is fully mediated by P(k).**

So the causal variable is not the competence gap. It is **the number of correct peers**, and
the response is close to a step:

- **0 correct → −0.45.** Catastrophic. The subject abandons a correct answer it already had.
- **1 correct → −0.01.** Neutral. One right peer is enough to stop the damage entirely.
- **2 correct → +0.20.** Helpful.

Competence matters only because it sets P(zero correct peers). `report` prints this
decomposition directly (`experiments/008-competence-gap/run.py`).

## Consensus is not the mechanism, and I predicted it would be

Seeing the P65 split first — "agree, both wrong" at −0.556 against "disagree" at −0.063 — I
proposed that wrong *consensus* was doing the damage and that competence was a proxy for it.
The full decomposition says no. Splitting agreement from correctness, two wrong peers that
**differ** are about as harmful (−0.400, −0.429) as two that **agree** (−0.556, −0.447), and
at P15 agreement is very slightly *less* harmful. The "disagree" row looked safe at P65 only
because at that accuracy it mostly contained *one correct peer*, which is the protective
condition. Agreement was confounded with correctness, and I read the confound as the cause.

## What it explains

- **004's net exactly zero at gap 0.** Peers at 0.69 almost always supply at least one
  correct answer, so the run sat in the k=1 and k=2 buckets, which roughly cancel. 008's
  P65 is that replication and lands at +0.065 — the same near-zero, with the sign explained.
- **005's −0.123 cross-family.** llama and mistral at 0.19/0.29 produce zero-correct blocks
  often, but not as often as P15's 0.18 pair — and the harm is milder in proportion.
- **Why "deliberation hurts" and "deliberation helps" are both true in this repo.** They are
  the same function read at different peer accuracies. There is no contradiction to resolve
  between 001 and 004; there is one curve and two sampling points on it.

## What it implies

The deployable rule is not "don't deliberate" and not "match panels on competence". It is
**make sure at least one member is likely to be right**, which is a much weaker and cheaper
condition than raising everyone's competence. A panel of one strong and two weak members
should be safe, where three uniformly mediocre members are not — and that is testable
directly, since it predicts the *composition* that matters is max(member accuracy), not mean.

That also recasts the Condorcet framing 003 and 005 used. Majority voting asks whether the
mean member clears a threshold. This says deliberation asks whether the *best* member is
present in the block at all. Two different statistics, and the second is the one that moved.

## Weaknesses

- One model, one task family, depth 4 — the standing limitation since 001.
- Peers are weak *samples* of a competent model, not a genuinely weaker model. A real weaker
  model may produce errors of a different character, and the README flagged this in advance.
- The 139-task set excludes tasks qwen always or never gets right, so it is harder than the
  full pool (solo 0.647 vs 0.692) and the magnitudes do not transfer to it. The ordering and
  the within-bucket stability are what this measures.
- **"2 correct" at P15 is n=1 and "0 correct" at P80 is n=3.** The corner cells of the table
  carry nothing on their own; the pooled column is what the claim rests on.
- **Peer correctness is not independent of task difficulty across the set.** Within a task the
  peers are real draws, but a task with 5 wrong draws out of 6 is a harder task, and at low p it
  is more likely to land in the 0-correct bucket. The within-bucket stability across conditions
  argues against this driving the result — the same bucket gives the same delta whether it was
  reached at P65 or P15 — but it is not ruled out by design.
- **The mixture fit has three free constants and five points to hit.** It is a good fit, not an
  overdetermined one. What makes it more than a curve-fit is that the constants are estimated
  per bucket and the *condition* never enters; but a sixth condition would test it properly.
