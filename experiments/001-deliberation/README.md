# 001 — Does deliberation between agents beat one agent, at matched cost?

**Status:** phase 1 running (2026-08-30). **Hypothesis stated before any arm was run.**

## Question

Multi-agent systems routinely have agents confer before answering. The claim is that
discussion improves the answer. The usual evidence compares k communicating agents against
one agent, which is not a controlled comparison: k agents spend k times the tokens, so any
gain is confounded with simply sampling more.

The comparison that isolates communication is against **k agents that do not communicate**.

## Hypotheses

- **H1.** Majority vote over k independent samples beats a single sample. (Ensembling works.)
  Prior evidence: at n=60, +0.083 with paired McNemar p=0.227 — a trend, not established.
  Powered here at n=195.
- **H2 (the question).** Deliberation beats non-communicating agents **at equal total tokens**.
  Stated as a directional prediction rather than a hope: we expect **H2 to fail** on this task.
  A reporting-chain lookup has a verifiable answer and no division of labour, so an agent
  reading three peer answers gains little information it could not get by re-deriving, while
  gaining a strong social prior toward the majority.
- **H3.** Deliberation raises inter-agent **agreement** more than it raises accuracy. If so,
  consensus becomes a worse predictor of correctness after discussion than before — the
  measurement that would be missed by an accuracy-only score.
  Baseline from probe 6: unanimous k=3 was 7/9 correct, all-three-differ was 1/7.

## Design

n=195, `multi_hop` depth 4, temperature 0.7, `qwen2.5` 7B, seeds 5000–5194.

n was chosen by a power calculation, not by convenience: from the observed discordance rate
(0.183) and split (8:3) at n=60, resolving an effect of that size at 80% power needs ~35
discordant pairs, hence n≈195. Seeds overlap probe 6's block so the earlier run replays as a
prefix.

**Phase `samples`** — 7 independent samples per task. Arm A is the k=1 prefix; arm C at
k∈{1,3,5,7} is the k-prefix of the *same* draws. One sweep yields the whole cost curve, and
the arms share sampling noise instead of each drawing its own.

**Phase `deliberate`** — arm D. Reuses the first 3 samples as round one, shows each agent the
other two full responses, takes one revision round, and votes over the revised answers. D
shares its history with C rather than drawing independently.

## What counts as an answer

C is reported as a curve of accuracy against total tokens; D is a point. **H2 is supported only
if D lies above that curve.** Comparing D to C at equal k gives D a free extra round and is the
usual way this result gets overstated.

Because arms run on identical task instances, comparisons are paired (exact McNemar), not
marginal-interval overlap. Task-set variance (0.163) is three times run-to-run variance (0.050),
so arms sharing instances is a requirement, not a convenience — see
`notes/2026-08-30-instrument-findings.md` and `reports/2026-08-30-calibration.pdf`.

## Known weaknesses

- One task family. A lookup task may be the least favourable case for deliberation; a task with
  separable subgoals could plausibly go the other way, and that is a different experiment.
- One model, and a small one. Whether the effect depends on capability is the interaction 002's
  roster is meant to probe.
- The revision prompt tells agents the peers "may all be wrong", which pushes against conformity.
  A neutral phrasing would likely show more herding; the honest version reports both.
