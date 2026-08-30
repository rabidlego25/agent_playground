# 001 — Does deliberation between agents beat one agent, at matched cost?

**Status:** complete (2026-08-30). **Hypotheses stated before any arm was run.**
**Result: H1 confirmed, H2 rejected as predicted, H3 supported.**
**Arm B, added after the fact, outranks every arm above and reframes all of them.**

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

## Arm B — one agent, added after the pre-registration (2026-08-30, n=195)

Arm B was not in the original design. It was added because the design had no answer to the
obvious practitioner question: if k agents cost k times as much, what does one agent do with
the same money? The planned version — same prompt, larger token cap — is dead on arrival.
The 400-token cap bound **1 of 1365** completions and mean output was 112 tokens, so raising
it buys nothing. The model has to be *asked* to do more work, not permitted to.

Asking changes two things at once, so B splits them: whether the model is told to reason,
and whether an output notation is imposed on it.

| arm | acc | 95% CI | total tokens | vs. A, paired |
|---|---|---|---|---|
| **B1n: reason step by step, no notation** | **0.72** | [0.66, 0.78] | **51,898** | +0.21, p<0.0001 |
| B3n: same, three attempts, one context | 0.50 | [0.43, 0.57] | 86,220 | −0.01, p=0.81 |
| B3: three attempts, notation imposed | 0.31 | [0.25, 0.38] | 75,596 | −0.20, p<0.0001 |
| B1: one attempt, notation imposed | 0.27 | [0.21, 0.34] | 50,415 | −0.24, p<0.0001 |

**One sentence of prompt beats every multi-agent arm at a tenth the cost.** B1n adds
"Before answering, work through the reporting chain step by step" and nothing else. It
reaches 0.72 for 51,898 tokens — cheaper than a single bare sample, above the seven-way
vote (0.63 for 376,156) and above deliberation (0.61 for 500,045).

### The finding that pays for the arm

| | one context | k contexts |
|---|---|---|
| 1 derivation | B1n **0.73** | A 0.51 |
| 3 derivations | B3n **0.51** | C3 **0.58** |

Three derivations in one context are **significantly worse** than one (p<0.0001). Three in
separate contexts are **significantly better** than one (p=0.0125). Same model, same task,
same derivation count; the only difference is whether the derivations can see each other.
Per-attempt output length is identical (76 vs ~75 tokens), so this is not a budget effect —
the model copies its first attempt into the next two, and a vote over three copies of one
derivation returns the bare-prompt baseline exactly (0.51 against 0.52).

This is the third independent test of the correlation account in the H2 section, and the
strongest, because it is a **loss** rather than a null. Deliberation gave a null. In-context
repetition gives a real decrement. Both spend the error independence that voting depends on.

### Two prompt bugs, kept in the record

Both were invisible in the aggregate score and obvious within thirty seconds of reading raw
completions. Both are mine.

**Numeric interference.** The first version said "work the chain *seven* separate times" on a
task asking "who is *4* levels above X". qwen2.5 read the seven as the hop count, walked
seven links, and answered the seventh name. B7 scored 0.27 against B3's 0.83 for that reason
alone. Digits in an instruction wrapped around a counting task are a confound. That trace is
discarded, not committed; the corrected arms label attempts A/B/C and contain no digits.

**Format suppression.** The replacement asked the model to "write each link as
`<name> -> <manager>` and count the links as you go". The notation has no slot for a count,
so the model obeyed the notation and dropped the count, walking to the top of the chain
instead of stopping at the requested depth:

```
bare prompt (arm A), correct          notation imposed (arm B1), one link too far
  1. Rhea reports to Talos.             Rhea -> Talos
  2. Talos reports to Altair.           Talos -> Altair
  3. Altair reports to Elara.           Altair -> Elara
  4. Elara reports to Draco.            Elara -> Draco
  ANSWER: Draco   <- gold               Draco -> Iris
                                        ANSWER: Iris
```

The bare prompt spontaneously **numbers** its steps, and the numbering is what enforces the
stop. Imposing a notation removed it, and cost 0.24 accuracy while cutting output from 112
tokens to 36. B1/B3 are kept and reported at full n because they are a clean measurement of
exactly that: imposed format against unimposed, identical tasks, paired.

### What this does to the rest of 001

It does not refute the arms above. They all shared the bare prompt, so the comparisons
between them stand: ensembling really does beat a single sample, and deliberation really does
not beat non-communicating agents at matched cost.

It does relocate them. The whole ensembling curve lives between 0.51 and 0.63, and a one-line
prompt change reaches 0.72 for free — so every configuration effect measured here fits inside
a band a single sentence moves you across. **The multi-agent question was being asked in a
regime where the model was not reasoning at all.** Before any of this is reported as a finding
about multi-agent systems, the C curve needs re-running on the B1n prompt: at a 0.72 base rate
the headroom is 0.28 rather than 0.49, and ensembling gains generally shrink as the base rate
rises. That is one sweep, and it decides whether 001 is a result about deliberation or a
result about a weak prompt.

## Follow-ups this opens

- **Mixed-family panel** (`003-mixed-panel/`) — the falsification test of the correlation
  explanation above. Same tasks, same seeds, panel of qwen2.5 / llama3.1 / mistral at matched
  size (7–8B) so family varies and capacity does not.
- **Re-run the C curve on the B1n prompt.** The single highest-value follow-up: it decides
  whether the ensembling result survives outside the weak-prompt regime. ~1,365 calls.
- **Planted wrong peer** — replace one peer with a confident plausible error. Separates
  information-following from conformity in the 50% mind-change rate. Reuses phase-1 traces.
- **A task family that decomposes.** `multi_hop` has no division of labour by construction. If
  that is why D failed, a task with separable subgoals should put D above the curve.

## Known weaknesses

- One task family. A lookup task may be the least favourable case for deliberation; a task with
  separable subgoals could plausibly go the other way, and that is a different experiment.
- **Every arm except B was measured on a prompt that does not ask the model to reason.** Arm B
  shows that prompt is worth 0.21 to a single call. The configuration comparisons are internally
  valid and externally provisional until the C curve is re-run at the higher base rate.
- One model, and a small one. Whether the null is about deliberation or about *homogeneous*
  deliberation is what `003-mixed-panel/` was built to decide.
  roster is meant to probe.
- The revision prompt tells agents the peers "may all be wrong", which pushes against conformity.
  A neutral phrasing would likely show more herding; the honest version reports both.
