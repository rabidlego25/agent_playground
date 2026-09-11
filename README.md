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
| 006 | Where does the ensembling curve saturate on the reasoning prompt, and does `c` predict it? | complete | **0.877 at k=15 — inside the pre-registered band [0.86, 0.93], but the band also contained the named alternative (0.862), so `c` got no discriminating test.** Saturation is at k=5, one step later than bare, not the wide margin 004 implied. The answer is in at least one of 15 draws on **0.979** of tasks: plurality, not sampling, is now the bottleneck. [README](experiments/006-ensemble-asymptote/README.md) |
| 007 | Does role-specialised inter-agent routing beat one well-prompted agent, on a tool-using task? | **arm B parked**; harness, world and pool complete | Prediction committed before any run: **C > A > B**. Never tested — **the chosen add-on runs as a single agent on a repair task** (1 of 9 agents active, 0 inter-agent messages): its delegation is triggered by named research-paper workflows and none fits code repair, so arm B could only deliberate if we wrote the treatment ourselves. Produced four findings without its main comparison — free-tier quota mechanics, two trace-schema corrections that would have silently faked H2, and defect detectability. [README](experiments/007-openclaw-role-routing/README.md) · [PILOT](experiments/007-openclaw-role-routing/PILOT.md) · [SCREEN](experiments/007-openclaw-role-routing/SCREEN.md) · [ARM-B](experiments/007-openclaw-role-routing/ARM-B-PILOT.md) |
| 008 | Does deliberation harm track the competence gap, or family mismatch? | complete | **The gap, and 005 needs no family explanation** — delta runs +0.180 / +0.101 / +0.065 / −0.115 / **−0.360** as peer accuracy falls 1.00 → 0.15 (H1 monotone, H2 and H3 both confirmed), where 005's cross-family −0.123 at a comparable gap is 2.9× milder. **But the gap is not the cause.** Bucketed by how many peers were correct, the delta is identical in all five conditions (0 → −0.45, 1 → −0.01, 2 → +0.20) and only the *shares* move (0-correct 0% → 81%); those three constants reproduce every condition's aggregate to within the 0.050 noise floor. **One correct peer is enough to stop the damage.** [README](experiments/008-competence-gap/README.md) |
| 009 | Is deliberation harm set by P(no correct peer), or by mean peer competence? | complete | **Neither — it tracks the *fraction* of peers that are correct.** Three peers instead of two breaks 008's count model exactly where count and fraction separate: k=1 is −0.132 here against −0.011 in 008 (n=234). Sorted by fraction the two experiments form one monotone curve that predicts all **eight** conditions leave-one-out with max residual **0.034**. **Refutes 008's "max, not mean"**: at identical max, raising mean 0.33→0.67 is worth **+0.209** (p=0.0002). [README](experiments/009-panel-composition/README.md) |
| 010 | Can the deliberation curve be used at runtime, or only described? | complete | **Usable, via a different observable.** Always-deliberate is −0.040; **deliberate only when every peer disagrees with you** is +0.061, a **+0.101** gain, firing on 28%. Held out on two prompts: +0.108, +0.095. Mechanism: deliberation is +0.481 when the agent was already wrong and **−0.287** when it was right, and P(wrong | all peers agree) = **0.032**. Zero new model calls. [README](experiments/010-gating/README.md) |

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

Updated 2026-09-11. The shared harness (`lib/trace.py`, `lib/tasks.py`, `lib/models.py`) and the
instrument probes in `tests/` are in place and calibrated (`reports/2026-08-30-calibration.pdf`:
task-set variance 0.163, run-to-run 0.050). 001, 003, 004, 005, 006, 008, 009 and 010 are complete; 002 is
designed and unrun; 007's arm B is parked after its scaffold turned out not to be one.

The harness gained its first multi-step world on 2026-09-10: `lib/worlds/repair.py` generates a
workspace an agent works in rather than a prompt it answers, and `tests/probe_repair_world.py`
asserts four oracle properties per instance before any run. Writing that probe rejected four of
twelve mutation cells and caught a bug in the oracle itself — `__pycache__` travelled with the
workspace copy, so a stale `.pyc` could score the module the agent had already replaced.

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

006 was the first attempt to make `c` pay rent, and it half-failed. k=15 landed at 0.877, inside
the pre-registered [0.86, 0.93] — but the named alternative, 0.862, was inside that band too, so
the run could not say which estimator was right. **A band that contains the rival prediction
cannot be wrong and therefore cannot be informative**; the next pre-registration here has to
exclude it. What 006 did settle: saturation on B1n is at k=5 (one step later than bare, not the
wide margin 004 implied), the plateau sits at ~0.88, and the correct answer is present in at
least one of 15 draws on 0.979 of tasks — so plurality selection, not sampling, is what now
costs the most. Building the prediction had already produced one methodological result at zero
token cost:
bootstrap resampling from a small draw pool under-predicts vote accuracy by 0.12–0.15 when
extrapolating ~2×, because it cannot reproduce how concentrated the true answer distribution is.
That disqualified the estimator the pre-registration was going to use, and it was only checkable
because 004's traces were kept — replay over re-run, paying off directly.

007 moved the deliberation claim to a tool-using runtime and never got to test it, but it paid
for itself in instrument work. The task world was parameterised after its first screen put one
agent at 7/7 — effective n went from 12 cells to 37 of 40 — and the trace exporter caught two
errors in the pilot's own notes that would have corrupted the result while looking fine: the
per-request event fires once per *run*, not per call, and every token figure reads 0 unless the
provider's `supportsUsageInStreaming` compat flag is set. Its final answer was negative and
cheap: **the nine-agent add-on chosen as "a configuration people actually deploy" is a scripted
research-paper pipeline**, whose delegation fires on named workflows (paper-pipeline, rebuttal,
daily-digest) and which, pointed at a bug, runs as one agent with zero inter-agent messages. Six
requests to avoid a 13–23 day run. Its shipped inter-agent config does not even load on the
current runtime. See `ARM-B-PILOT.md`.

008 then answered 005's open question for ~2 hours of local compute, using peers assembled from
004's stored draws — replay over re-run again. Five conditions, n=139 each, no API cost. All three
pre-registered predictions hold: the delta declines monotonically with peer accuracy (H1),
**deliberation harm tracks the competence gap and not family mismatch** (H2: −0.360 at gap −0.47
against 005's −0.123 cross-family), and peers who are all correct *help* by +0.180 (H3) — which
falsifies the stronger reading 004 invited, that peer answers are noise to an agent that has
already worked the chain.

The decomposition overturns the framing the experiment was built on. Bucketed by how many peers
were correct, the delta is the *same* in every condition — 0 correct −0.448, 1 correct −0.011,
2 correct +0.202 — and only the mixture weights move. Feeding each condition's P(k) through those
three constants reproduces its aggregate delta with residuals of at most 0.022, all inside the
0.050 noise floor: **peer accuracy is fully mediated by P(at least one correct peer)**, and the
response is close to a step. Competence matters only because it sets P(zero correct peers). That
dissolves the apparent conflict between 001 and 004: "hurts" and "helps" are one curve read at two
peer accuracies. See `notes/2026-09-11-one-correct-peer-is-enough.md`.

009 then tested 008's closing claim instead of building on it, and refuted it. 417 more
local calls, no API cost. **The variable is the fraction of peers that are correct, not the
count.** 008's per-k constants were fitted entirely on two-peer blocks, where count and
fraction are the same thing; at three peers they miss k=1 by 0.121 on n=234, because one
correct peer is a tie in a pair and a minority in a trio. Sorted by fraction, both
experiments lie on one monotone curve that predicts all eight of their conditions
leave-one-condition-out with a maximum residual of 0.034. And **max is not the composition
statistic**: holding max at 1.00 and moving mean peer accuracy 0.33 → 0.67 is worth +0.209
(p=0.0002). "One correct peer is enough" was an artifact of measuring pairs. See
`notes/2026-09-11-fraction-not-count.md`.

010 then asked whether any of the deliberation work is usable, and answered it from traces
already on disk — 1,170 measured instances, zero new model calls. **It is, but not through the
variable 008 and 009 pointed at.** The fraction of correct peers is unobservable at runtime;
peer *disagreement* is free, and it is what matters: deliberation is worth **+0.481** when the
agent was already wrong and **−0.287** when it was already right, where it is capped at zero
and can only take a correct answer away. P(wrong | every peer agrees with me) is **0.032**. So
gating on "every peer disagrees with me" turns always-deliberate's −0.040 into **+0.061**, a
+0.101 gain, and it holds on both prompts without fitting (+0.108, +0.095).

That reframes 008 and 009 rather than overturning them: they fixed the subject's answer and
selected peers independently of it, so their curve is the causal effect of composition. In a
real panel, peers and subject are the same model on the same task, so the fraction-correct
curve is substantially a proxy for "is the subject wrong". See
`notes/2026-09-11-deliberate-only-when-peers-disagree.md`.

Next: **007's ladder is built and unrun**, waiting on free-tier quota, and it is the only
thread that tests role specialisation rather than deliberation. The 0.102 gap between 006's
0.979 oracle ceiling and its 0.877 vote is still the largest thing on the table, and it is a
selection problem rather than a sampling one.
one.
002 is designed and unrun. 005 still owes a pre-registered llama3.1 re-run at max_tokens=1600.
007's repair world, oracle, sandbox, exporter and calibrated pool all survive its arm B and are
reusable by anything that needs a tool-using task with a programmatic oracle — what it lacks is a
multi-agent scaffold that is actually general.
