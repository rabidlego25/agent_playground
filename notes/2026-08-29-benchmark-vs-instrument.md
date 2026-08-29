# The benchmark is the instrument, not the object

**Date:** 2026-08-29. Prompted by the observation, mid-build, that "so this is a benchmark."

## The confusion worth not having

Yes: `lib/tasks.py` plus its oracles is a benchmark. That is deliberate and load-bearing. It is the
**dependent variable** — you cannot ask whether a configuration helps without something that scores.
Procedural generation, programmatic oracles and the delimited `ANSWER:` field exist to make that
measuring stick honest, nothing more.

The six probes in `tests/` are **not** benchmarking. They are instrument calibration:

| probe | what it characterises | why it is not a score |
|---|---|---|
| `probe_variance_floor` | same-condition run-to-run spread | sets the minimum detectable effect; any later result smaller than this is noise |
| `probe_depth_curve` | where the task has dynamic range | picks the operating point; a task at ceiling or floor measures nothing |
| `probe_distractor_load` | chain-length vs. context-noise as the failure driver | separates two mechanisms that look identical in an aggregate score |
| `probe_order_sensitivity` | sensitivity to fact ordering | a nuisance parameter to hold fixed or randomise |
| `probe_name_scramble` | contamination resistance | validates the premise of procedural generation |
| `probe_self_consistency` | single-sample vs. k-sample lift | the baseline any communication arm has to beat |

None of these produce a number anyone should care about on its own. They describe the apparatus
before it gets used. **A probe result that looks impressive is a probe that was misdesigned.**

## The variable assignment that keeps this a research project

- **Independent variable:** agent configuration — 1 vs. k agents, communication vs. none, role
  decomposition, handoff structure, stopping rules.
- **Dependent variable:** task success, cost, and variance, measured by the benchmark.
- **Model: a blocking factor, not a treatment.** Vary it to check that a configuration effect
  survives a change of substrate. Do not vary it to rank it.

The drift to guard against is easy and seductive: benchmarks emit numbers, numbers feel like
progress, and "which model wins" is the cheapest number to produce. It is also a crowded and
short-lived question — a model leaderboard is stale in a quarter, which is exactly wrong for a
project intended never to finish. A finding about *configuration* outlives the models it was
measured on. That is the whole reason for the provider-agnostic rule in `CLAUDE.md`.

**Test for whether a planned run belongs here:** if the headline would name a model, it is probably
a leaderboard entry. If the headline names a configuration and the models are the error bars around
it, it is this project.

## What the frame changed in practice

A model roster drafted under the wrong frame ("which models should we compare") got re-ranked under
the right one ("which substrates let me test whether a configuration effect generalises"):

- `qwen3:8b` — **promoted.** Its thinking toggle is not a model comparison at all. Same weights, one
  flag, internal vs. external deliberation. That is a *configuration* contrast that happens to be
  implemented as a model feature, and a rare clean one.
- `qwen2.5:3b` / `7b` / `14b` — kept, different justification. Not "how does scale score" but the
  interaction: **does deliberation substitute for capability?** If multi-agent gains shrink as models
  improve, these configurations are a small-model crutch with a shelf life. Needs ≥3 capability points.
- Pairwise error correlation across models — kept. It is a *precondition of the ensemble mechanism*
  (voting only helps if errors decorrelate), not a ranking.
- `gemma3` / `phi4` — dropped for now. Under the wrong frame they were "diversity". Under the right
  one they test nothing specific.

## Corollary: the notes are instruments too

These notes are not only for human readers. They are the artifact a future agent — after a
compaction, or in a fresh session — reads to reconstruct why things are the way they are. That makes
note format an **independent variable in exactly the sense above**, and one this project is unusually
well placed to test, since it already has a scoring harness and a handoff-tax question queued.

Testable, with the existing rig:

- Fix a task. Have agent A solve it and write a handoff note under format F. Have agent B continue
  from the note alone. Sweep F: prose vs. structured; conclusions-only vs. conclusions-plus-rejected-
  alternatives; with vs. without raw evidence pointers. Measure B's accuracy and token cost.
- The `notes/` directory here is already an unintentional natural experiment: the oracle note leads
  with the failure and includes the rejected fixes; the decision note leads with the conclusion.
  Which one better prevents a re-derivation is measurable, not a matter of taste.
- Specific hypothesis worth its own experiment: **recording rejected alternatives is the highest-value
  part of a note**, because it is the part that prevents a re-derivation loop, and it is the part
  every summarizer drops first. Compaction is lossy in a *biased* direction — it keeps conclusions and
  discards the search that produced them.

If that holds, it is a finding about agent memory generally, not about this repo's housekeeping.
