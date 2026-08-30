# The prompt moved the number further than any configuration did

2026-08-30. From `experiments/001-deliberation/`, n=195, `multi_hop` depth 4, qwen2.5 7B,
identical task instances throughout, all comparisons paired (exact McNemar).

| arm | acc | total tokens |
|---|---|---|
| 1 call, "work through it step by step", no notation imposed | **0.72** | 51,898 |
| 7 independent samples, majority vote | 0.63 | 376,156 |
| 3 samples + a round of deliberation | 0.61 | 500,045 |
| 1 call, bare prompt | 0.51 | 53,814 |
| 1 call, output notation imposed | 0.27 | 50,415 |

The configuration axis — one agent, seven agents, agents that talk — spans 0.51 to 0.63.
The prompt axis spans 0.27 to 0.72 on the same model and the same tasks, and the best
point on it is also the cheapest.

## Why this is a note and not just a result

The multi-agent literature this experiment was built to test reports gains in the 0.05–0.10
band. That band is smaller than the noise the prompt introduces. Any such comparison that
does not hold the prompt fixed *and* report where on the prompt axis it is sitting is
reporting an effect smaller than an uncontrolled variable in the same experiment.

001 holds the prompt fixed, so its internal comparisons stand. What it cannot claim is that
they generalise, because they were all measured at 0.51 — the regime where the model was not
reasoning. Ensembling gains shrink as the base rate rises, and the k=3 vote may have nothing
left to fix at 0.72.

**The operational rule this suggests:** before running a configuration sweep, find the top of
the prompt axis for that task and model, and run the sweep there. A configuration effect
measured below the prompt ceiling is a measurement of how much the configuration compensates
for a bad prompt. That is a real quantity, but it is not the one anyone thinks they are
reporting.

## Sharing a context is not the same as sampling more

The clean cell in the design, and the reason the arm paid for itself:

| | one context | k contexts |
|---|---|---|
| 1 derivation | 0.73 | 0.51 |
| 3 derivations | 0.51 | 0.58 |

Three derivations in one context are significantly *worse* than one (p<0.0001). Three in
separate contexts are significantly *better* than one (p=0.0125). Derivation count is held
fixed; per-attempt output length is within a token (76 vs ~75). The model copies its first
attempt into the next two, and a vote over three copies of one derivation returns the
bare-prompt baseline exactly (0.51 against 0.52).

This is the same mechanism as 001's deliberation null, seen a third time and with a sign
this time rather than a null: **anything that lets k derivations see each other spends the
error independence that voting depends on.** Deliberation spends it and breaks even. In-context
repetition spends it and loses.

## A formatting instruction suppressed the reasoning it was written to support

The 0.27 row is not a weak prompt. It is the *same* instruction as the 0.72 row —
"count the links as you go" — plus a notation: write each link as `<name> -> <manager>`.

The notation has no slot for a count. The model obeyed the notation and dropped the count,
walking to the top of the chain instead of stopping at the requested depth. Output fell from
112 tokens to 36. The bare prompt, which imposes nothing, spontaneously numbers its steps,
and the numbering is what enforces the stop.

Asking a model to reason and simultaneously handing it a format with nowhere to put the
reasoning gets the format. Cost here: 0.24 accuracy, p<0.0001, against a prompt that asked
for *more* thinking.

See also [`2026-08-29-oracle-format-confound.md`](2026-08-29-oracle-format-confound.md) —
the same shape a third time. Output format keeps turning out to be load-bearing on tasks
where it looks cosmetic.

## Both bugs were invisible in the aggregate and obvious in the raw text

The first arm-B prompt said "work the chain *seven* separate times" on a task asking who is
*4* levels above X. qwen2.5 read the seven as the hop count and answered the seventh name;
B7 scored 0.27 and B3 scored 0.83 for that reason alone. A digit in an instruction wrapped
around a counting task is a confound.

Both times the score was plausible. 0.83 read as a headline, 0.27 read as a collapse, and
they were one bug with opposite signs. Thirty seconds of reading completions found each.
**Read ten raw completions per arm before believing any number it produces** — the same
discipline the oracle bug argued for, and the same failure mode when skipped.
