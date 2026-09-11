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
| 008 | Does deliberation harm track the competence gap, or family mismatch? | H2 complete; H1/H3 running | **The gap, and 005 needs no family explanation** — delta +0.065 at gap 0.00 vs **−0.360** at gap −0.47 (McNemar 68/9, p<1e−6), where 005's cross-family −0.123 at a similar gap is 2.9× milder. **But the gap is not the cause.** Bucketed by how many peers were correct, the delta is identical in both conditions (0 → −0.44, 1 → −0.04, 2 → +0.27) and only the *shares* move (0-correct 10% → 81%). **One correct peer is enough to stop the damage.** [README](experiments/008-competence-gap/README.md) |

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
task-set variance 0.163, run-to-run 0.050). 001, 003, 004, 005, 006 and 008's H2 are complete; 002 is
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

008 then answered 005's open question for 77 minutes of local compute, using peers assembled from
004's stored draws — replay over re-run again. **Deliberation harm tracks the competence gap and
not family mismatch** (−0.360 at gap −0.47 against 005's −0.123 cross-family). But the
decomposition overturns the framing the experiment was built on: bucketed by how many peers were
correct, the delta is the *same* in both conditions and only the mixture weights move. **The
causal variable is the number of correct peers, not the gap**, and the response is close to a
step — 0 correct ≈ −0.44, 1 correct ≈ −0.04, 2 correct ≈ +0.27. Competence matters only because
it sets P(zero correct peers). That dissolves the apparent conflict between 001 and 004: "hurts"
and "helps" are one curve read at two peer accuracies. See
`notes/2026-09-11-one-correct-peer-is-enough.md`.

Next: **008's rule needs its own test — if one correct peer is enough, the composition statistic
that matters is max(member accuracy), not mean**, which is a different quantity from the Condorcet
threshold 003 and 005 were built around and predicts a 1-strong/2-weak panel is safe where three
mediocre members are not. The 0.102 gap between 006's 0.979 oracle ceiling and its 0.877 vote is
still the largest thing on the table, and it is a selection problem rather than a sampling one.
002 is designed and unrun. 005 still owes a pre-registered llama3.1 re-run at max_tokens=1600.
007's repair world, oracle, sandbox, exporter and calibrated pool all survive its arm B and are
reusable by anything that needs a tool-using task with a programmatic oracle — what it lacks is a
multi-agent scaffold that is actually general.
