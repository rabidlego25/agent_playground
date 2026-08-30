# 001 — Does deliberation between agents beat one agent, at matched cost?

**Status:** complete (2026-08-30). **Hypotheses stated before any arm was run.**
**Result: H1 confirmed, H2 rejected as predicted, H3 supported.**

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

## Results (2026-08-30, n=195)

| arm | acc | 95% CI | tokens in | tokens out | total |
|---|---|---|---|---|---|
| A: single sample | 0.513 | [0.44, 0.58] | 31,838 | 21,976 | 53,814 |
| C: k=3 vote, no comms | 0.585 | [0.51, 0.65] | 95,514 | 66,683 | 162,197 |
| C: k=5 vote, no comms | 0.610 | [0.54, 0.68] | 159,190 | 110,792 | 269,982 |
| C: k=7 vote, no comms | 0.626 | [0.56, 0.69] | 222,866 | 153,290 | 376,156 |
| D: k=3 + one revision round | 0.610 | [0.54, 0.68] | 364,735 | 135,310 | 500,045 |

Exact McNemar on discordant pairs (arms share task instances, so all tests are paired):

| contrast | acc | first-only | second-only | discordant | p |
|---|---|---|---|---|---|
| A vs C3 | 0.51 → 0.58 | 7 | 21 | 28 | **0.0125** |
| A vs C5 | 0.51 → 0.61 | 7 | 26 | 33 | **0.0013** |
| A vs C7 | 0.51 → 0.63 | 13 | 35 | 48 | **0.0021** |
| C3 vs C5 | 0.58 → 0.61 | 5 | 10 | 15 | 0.302 |
| C3 vs C7 | 0.58 → 0.63 | 9 | 17 | 26 | 0.169 |
| C5 vs C7 | 0.61 → 0.63 | 6 | 9 | 15 | 0.607 |
| C3 vs D | 0.58 → 0.61 | 15 | 20 | 35 | 0.500 |
| C5 vs D | 0.61 → 0.61 | 20 | 20 | 40 | 1.000 |
| C7 vs D | 0.63 → 0.61 | 27 | 24 | 51 | 0.780 |

**H1 — confirmed.** Voting beats a single sample (A vs C3, p=0.0125). The n=60 null
(p=0.227) was underpowered exactly as the power calculation said. Returns saturate at k=3:
no adjacent-k step above 3 is significant, so k=7 costs 7× a single sample for +0.11.

**H2 — rejected, as pre-registered.** D reaches 0.610 for 500,045 tokens. C reaches the same
0.610 for 269,982. D is **1.85× the cost of the non-communicating control at identical
accuracy**, and lies below the cost curve rather than above it. Against every C point the
paired test is flat (p = 0.50, 1.00, 0.78).

**The mechanism is error correlation, not inertia.** Deliberation moved answers constantly —
292/585 agents (50%) changed their answer after seeing peers — and moved them net *toward*
the gold answer at the individual level:

| individual move | count |
|---|---|
| wrong → right | 129 |
| right → wrong | 93 |
| wrong → wrong | 70 |
| unchanged | 293 |

Net +36 individual corrections across 585 agent-slots, and the vote captured none of it. The
flips are correlated: agents move together. Majority voting's whole advantage is error
independence, and deliberation spends that independence at roughly the rate it buys
individual accuracy. This is the load-bearing claim and it is the one to attack — the direct
test is a **mixed-family panel**, where three different model families cannot converge as
easily. If D still fails there, this explanation is wrong.

**H3 — supported.** Agreement rose while accuracy did not, and consensus lost diagnostic
value:

| distinct answers among 3 | pre: tasks | pre: majority correct | post: tasks | post: majority correct |
|---|---|---|---|---|
| 1 (unanimous) | 58 | 0.78 | 93 | 0.78 |
| 2 | 109 | 0.57 | 90 | 0.47 |
| 3 | 28 | 0.25 | 12 | 0.33 |

Unanimity rose 0.30 → 0.48 with reliability flat at 0.78. Thirty-five additional tasks now
look confident and are correct at exactly the base rate of the previously-confident group.
Post-deliberation consensus is a strictly worse signal than pre-deliberation consensus: same
reliability, applied to 60% more cases. An accuracy-only score would report "no change" and
miss that the confidence signal degraded.

## Follow-ups this opens

- **Mixed-family panel** (`003-mixed-panel/`) — the falsification test of the correlation
  explanation above. Same tasks, same seeds, panel of qwen2.5 / llama3.1 / mistral at matched
  size (7–8B) so family varies and capacity does not.
- **Arm B** — one agent given k× the token budget. The design above has no such arm, and it is
  the control a practitioner actually cares about: if one agent thinking longer beats a k-way
  vote, the multi-agent framing is answering the wrong question.
- **Planted wrong peer** — replace one peer with a confident plausible error. Separates
  information-following from conformity in the 50% mind-change rate. Reuses phase-1 traces.
- **A task family that decomposes.** `multi_hop` has no division of labour by construction. If
  that is why D failed, a task with separable subgoals should put D above the curve.

## Known weaknesses

- One task family. A lookup task may be the least favourable case for deliberation; a task with
  separable subgoals could plausibly go the other way, and that is a different experiment.
- One model, and a small one. Whether the null is about deliberation or about *homogeneous*
  deliberation is what `003-mixed-panel/` was built to decide.
  roster is meant to probe.
- The revision prompt tells agents the peers "may all be wrong", which pushes against conformity.
  A neutral phrasing would likely show more herding; the honest version reports both.
