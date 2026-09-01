# agent_playground

An ongoing lab for agentic systems — configurations, workflows, benchmarks, evaluation methods.
Reproducible, provider-agnostic, and designed to accumulate rather than conclude.

Agentic infrastructure is permanent; the models are not. This repo exists to build up durable
evidence about how agents actually behave in workflows, across whatever models happen to be
current. There is no roadmap and no end state. The unit of progress is a dated experiment with a
stated hypothesis and a trace someone else could re-analyze.

## Experiments

| ID | Question | Status | Verdict |
|----|----------|--------|---------|
| 001 | Does deliberation between agents beat a single agent, at matched tokens? | complete | **No.** 1.85× the cost of non-communicating agents for identical accuracy. One line of prompt beats every arm at a tenth the cost. [README](experiments/001-deliberation/README.md) |
| 002 | Does rhetorical packaging change what a reader agent does, at equal information? | designed | [README](experiments/002-rhetoric-vs-information/README.md) |
| 003 | Does a mixed-family panel restore what deliberation destroys? | complete | **Untestable as designed.** The 3-way vote lands below its best member (p=0.007). What survives: deliberation transferred capability to the weakest member (+0.13) without costing the strongest. [README](experiments/003-mixed-panel/README.md) |
| 004 | Does the ensembling gain survive at the top of the prompt axis? | samples complete, D′ running | **Yes, and it grows.** Voting still beats one sample on the reasoning prompt (p=0.0094); the k=7 gain rose +0.113 → +0.195 because the prompt made errors *more* independent (c 0.339 → 0.239). At matched tokens the k=7 vote goes 0.63 → 0.86. [README](experiments/004-prompt-ceiling/README.md) |

Keep this table current. A repo of fifty experiments with no index is write-only — you re-run what
you already answered.

## How work here is done

- **State the hypothesis before the run.** A README with only results is a log, not an experiment.
- **The trace is the artifact.** Every run appends a step-level JSONL episode to `results/`, so a
  finding can be re-analyzed without re-paying for it. Prefer replay over re-run.
- **Generate tasks, don't collect them.** Procedural generation with programmatic oracles buys
  contamination resistance, a difficulty knob, and unlimited n at zero token cost.
- **Report n and variance.** A single run of a stochastic agent configuration is an anecdote.
- **Date everything, absolutely.** Model capabilities move; an undated result is unreadable later.
- **Stay provider-agnostic.** Model access goes through one adapter in `lib/`, never vendor calls
  scattered through experiment code.

## Layout

```
experiments/   one dir per experiment: NNN-slug/ with hypothesis, code, runs
benchmarks/    harnesses for and analyses of existing suites
lib/           shared code — model adapters, task generators, trace schema
notes/         ideas, theory, open questions, decision records
results/       raw run artifacts, append-only
```

`CLAUDE.md` holds the working conventions and current environment constraints.
`notes/open-questions.md` is the running list of things worth attacking.

## Status

Updated 2026-09-01. The shared harness (`lib/trace.py`, `lib/tasks.py`, `lib/models.py`) and the
instrument probes in `tests/` are in place and calibrated (`reports/2026-08-30-calibration.pdf`:
task-set variance 0.163, run-to-run 0.050). 001 and 003 are complete; 004 is running; 002 is
designed and unrun.

Both completed experiments landed on the same open question, which is what 004 is: every
configuration effect measured so far was measured on a prompt that does not ask the model to
reason, and one sentence of prompt is worth more than any configuration in the sweep. Until 004
lands, treat 001's and 003's configuration findings as internally valid and externally
provisional. See `notes/2026-08-30-prompt-dominates-configuration.md`.
