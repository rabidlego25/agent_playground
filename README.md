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
| 004 | Does the ensembling gain survive at the top of the prompt axis? | complete | **Yes, and it grows.** Voting still beats one sample on the reasoning prompt (p=0.0094) and the k=7 gain rose +0.113 → +0.195, because the prompt made errors *more* independent (c 0.339 → 0.239). Deliberation is now significantly *worse* than not communicating (0.71 vs 0.86, p<0.0001) at 1.2× the cost. [README](experiments/004-prompt-ceiling/README.md) |
| 005 | Does the mixed panel clear the Condorcet threshold once every member is prompted at its ceiling? | complete | **No, and the prompt made it worse.** The gain does not transfer: qwen2.5 +0.154, mistral +0.108, llama3.1 −0.026. The vote now loses to its best member by 0.09 (p=0.0001) vs 0.08 in 003. Cross-family error independence stacks with prompting (c 0.249 → 0.211) — but independence without competence buys nothing. Deliberation cost the strongest member −0.123, where neither intervention alone cost it anything. [README](experiments/005-panel-at-ceiling/README.md) |
| 006 | Where does the ensembling curve saturate on the reasoning prompt, and does `c` predict it? | pre-registered, running | Prediction committed before any draw: k=15 = **0.89** [0.86, 0.93], with the plug-in estimator's ≤0.87 named as the alternative. The first out-of-sample test of `c`, the variable 003/004/005 all explain their results with. [README](experiments/006-ensemble-asymptote/README.md) |
| 007 | Does role-specialised inter-agent routing beat one well-prompted agent, on a tool-using task? | designed | Out-of-sample test of 001–005 against a deployed 9-agent OpenClaw config. Committed before any run: **C > A > B** — parallel-silent beats one good prompt beats the role panel, which spends ≥3× the tokens. [README](experiments/007-openclaw-role-routing/README.md) |

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
task-set variance 0.163, run-to-run 0.050). 001, 003, 004 and 005 are complete; 006 is
pre-registered and mid-sweep; 002 is designed and unrun.

001 and 003 both landed on the same open question — every configuration effect in them was
measured on a prompt that does not ask the model to reason. 004 closed it: the configuration
findings survive the prompt fix, and the deliberation result gets stronger, not weaker. The
working order that falls out of all five is **fix the prompt, then ensemble without
communication, and do not deliberate** — because a good prompt raises the base rate *and* buys
back the error independence a majority vote spends, while communication of any kind spends it.

005 attaches two conditions to that order. The prompt step is a property of the *pair* (prompt,
model), not of the prompt: the same sentence was worth +0.154 to qwen2.5, +0.108 to mistral:7b
and nothing at all to llama3.1. And the ensemble step needs members of comparable competence —
005 has the most independent errors measured in this repo (cross-family c=0.211, below either
intervention alone) and its vote still loses to its best member by 0.09, because two of three
sit under the Condorcet threshold. **Independence is not the binding constraint; competence is,
and independence only pays once members clear it.** Deliberation across that gap actively
damages the strong member (qwen2.5 −0.123), where neither the mixed panel nor the reasoning
prompt cost it anything on its own.
See `notes/2026-08-30-prompt-dominates-configuration.md`, `experiments/004-prompt-ceiling/` and
`experiments/005-panel-at-ceiling/`.

006 is the first attempt to make `c` pay rent. It has carried the argument three times and has
only ever been measured after the fact; 006 states a number for k=15 first and then measures it.
Building the prediction already produced one methodological result at zero token cost:
bootstrap resampling from a small draw pool under-predicts vote accuracy by 0.12–0.15 when
extrapolating ~2×, because it cannot reproduce how concentrated the true answer distribution is.
That disqualified the estimator the pre-registration was going to use, and it was only checkable
because 004's traces were kept — replay over re-run, paying off directly.

Next: 006's sweep is 51/195 and resumable; 002 is designed and unrun; and 005 owes a
pre-registered llama3.1 re-run at max_tokens=1600 (the cap bound on 11.8% of tasks — the
diagnostic says truncation is not the cause of its null, so this is a confirmation, not a
decider). 005's −0.123 to the strong member rests on two points, one of which also changes
family; a gap-dose curve reusing 004's seven qwen draws as peer blocks would separate
"harm tracks the competence gap" from "harm tracks family mismatch" for ~95 min of local
compute.
