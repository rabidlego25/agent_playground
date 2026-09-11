# Repair difficulty is set by detectability, not by how much code the fix touches

> **Retracted 2026-09-11, same day, by the held-out check this note's own experiment
> reserved.** Seeds 720–739 gave 1-edit **12/13 = 0.92** against the 6/11 = 0.55 below, and
> no 1-edit/2-edit gap at all (12/13 vs 7/7). The contrast this note is built on did not
> reproduce. The mechanism it proposes may still be right — the failures really do leave
> probe tests behind, in both runs — but **nothing here is evidence for it.** Left in place
> unedited because the reasoning is the useful part of the record. See `SCREEN.md` run 5.

**2026-09-11.** Measured while calibrating `lib/worlds/repair.py` for 007. n=20, arm A on
Gemini 3.5 Flash Lite, full tool surface, 0/20 rate-limited.

| defect | passed |
|---|---|
| 1-edit | 6/11 = 0.55 |
| 2-edit | **9/9 = 1.00** |

Fisher exact, one-sided, **p = 0.0298**. Defects requiring two coordinated edits were
*easier* than single-line ones, not harder.

This was a prediction made the wrong way round. The pool was hardened by making defects
span several edits, on the reasoning that a one-line fix is findable once the specification
is read. Multi-edit defects were verified to be genuine — generation reverts each edit in
turn and rejects the operator unless the module still fails with any one edit undone, and
the probe confirms it end to end through the real oracle (74 partial fixes, 0 wrongly
passed). They are really multi-edit. They are also really easier.

## The mechanism

Every one of the five failures left `test_*.py` files behind: `test_more.py`,
`test_comprehensive.py`, `test_bug.py`. The agent writes its own probes before fixing —
that is the loop working as intended.

A defect spanning two edits breaks more behaviour in more places, so the agent's own
probing finds it on the first try. A quiet single-line error survives that probing. The
four operators that failed every time they were drawn:

- `covered-fencepost` — `end - start` becomes `end - start + 1` inside a sum
- `no-count` — a rejection counter that stops incrementing
- `no-start-check` — a dropped guard clause
- `off-grid` — `<` becomes `<=` in a bounds check

All four are quiet and local. None changes the shape of the output; each shifts a value
or drops a case an ad-hoc test is unlikely to cover.

So the axis that sets difficulty for a tool-using repair agent is **how loud the defect is
under the agent's own testing**, not the size of the edit the fix requires. Those are
different axes and it is easy to assume the second is a proxy for the first.

Caveat on strength: per-operator rates come from 1–3 observations each and are anecdotes,
not rates. The defensible claim is the aggregate 1-edit vs 2-edit contrast at n=20, and
even that is one model on one task family. The *direction* is what matters here, because it
is opposite to the design assumption.

## What it implies for task design

A benchmark that tunes difficulty by making fixes bigger is tuning the wrong knob, and
would report a difficulty ordering that does not survive contact with an agent that tests
its own work. This is the repair-task analogue of the point in
[`2026-08-29-benchmark-vs-instrument.md`](2026-08-29-benchmark-vs-instrument.md): the
property you think you are varying and the property that moves the score are not
automatically the same, and only the second is measured.

It also suggests `discriminating` — the count of hidden cases a mutant breaks, already
recorded per instance — is the wrong proxy too. It did not separate pass from fail here
(failures spanned 2–9, passes 6–9). What matters is not how many of *our* hidden cases
break, but how likely the *agent's own* tests are to cover the broken case. That is a
harder thing to measure and a more interesting one.

## Open

- Does the ordering hold on a stronger model, or is it specific to Flash Lite's probing?
- Can detectability be estimated without a run — e.g. by generating plausible ad-hoc tests
  and measuring coverage of the broken case?
- 007 needs arm A near 0.60–0.70. `MULTI_EDIT_RATE` is set to 0.2 on the strength of this
  result, predicting 0.2 × 1.00 + 0.8 × 0.55 = **0.64**. That prediction is derived from
  the same n=20 that produced the finding, so it is stated here to be checked against
  held-out seeds rather than treated as established.
