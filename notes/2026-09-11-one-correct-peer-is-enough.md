# Deliberation harm is a step function of how many peers are right

**2026-09-11, from 008.** qwen2.5 at B1n, n=139 tasks, peers are qwen's own scored draws so
family, prompt, weights and temperature are identical to the subject and only peer accuracy
moves. The subject's round-one answer is the same draw in every condition, so conditions
pair exactly.

## The headline number, and why it is not the finding

| condition | peer accuracy | gap | delta |
|---|---|---|---|
| P65 | 0.64 | 0.00 | **+0.065** |
| P15 | 0.18 | −0.47 | **−0.360** |

Exact McNemar, discordant 68/9, p < 1e−6. 008's pre-registered H2 said a delta ≤ −0.10 at
P15 means harm tracks the competence gap. It does, by a wide margin — and 005's
cross-family −0.123 at a similar gap is **2.9× smaller**, so family mismatch is not needed
to explain deliberation harm and does not appear to add any.

That is the pre-registered answer. The decomposition is the actual finding.

## Bucket by how many peers were right

| peers | P65 n, delta | P15 n, delta |
|---|---|---|
| 0 correct, agree | 9, **−0.556** | 85, **−0.447** |
| 0 correct, differ | 5, −0.400 | 28, −0.429 |
| 1 correct, differ | 58, **−0.034** | 25, **−0.040** |
| 2 correct, agree | 67, +0.269 | 1, +1.000 |

**Within every bucket the delta is the same in both conditions.** Peer accuracy changes
nothing about what happens given a peer block; it changes only how often each block occurs.
The share of "0 correct" goes 10% → 81% between P65 and P15, and that mixture shift is the
entire aggregate effect.

So the causal variable is not the competence gap. It is **the number of correct peers**, and
the response is close to a step:

- **0 correct → ≈ −0.44.** Catastrophic. The subject abandons a correct answer it already had.
- **1 correct → ≈ −0.04.** Nearly neutral. One right peer is enough to stop the damage.
- **2 correct → +0.27.** Helpful.

Competence matters only because it sets P(zero correct peers).

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
  correct answer, so the run sat in the −0.04 and +0.27 buckets, which roughly cancel.
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
- "2 correct" at P15 is n=1 and carries nothing.
- P100, P40 and P80 were still running when this was written; H1 (monotonicity) and H3
  (transfer at peers-all-correct) are not yet in.
