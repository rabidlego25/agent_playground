# Open questions

Running list. Add freely; mark ones that become experiments with their experiment id.

## Configuration
- **[001]** Does pre-task communication between agents beat a single agent? Standing user question.
  The control that matters is k independent samples that never communicate — see
  `2026-08-29-starting-point-decision.md`. Note this is *not* the same as role decomposition:
  it varies deliberation, holding the agent set fixed.
- Does role specialization (planner / executor / critic) beat one strong model with the same total token budget?
  Token-matched comparison is the only fair version of this question, and almost nobody runs it that way.
- What is the actual marginal value of a critic pass? Hypothesis: it helps on tasks with a verifiable oracle
  and *hurts* on open-ended generation, where it regresses toward blandness.
- Context window vs. retrieval: at what task length does packing the window lose to targeted retrieval?
- Is there a measurable "handoff tax" per agent boundary — information lost when one agent summarizes for another?
  If so, it should be measurable as accuracy decay vs. number of hops on a task with a known answer chain.

## Model-to-role fit
- Cheap-model fan-out with a frontier-model synthesizer: where is the crossover point where the fan-out's noise
  costs more than the synthesizer can repair?
- Can a local 7B model do the *routing* decision well enough to save frontier calls? Routing is a
  classification problem, not a reasoning one — this may be the cheapest real win available.

## Benchmarks
- Most agent benchmarks measure task completion. Almost none measure cost-to-completion or variance across runs.
  A benchmark reporting mean-only for a stochastic system is reporting a third of the result.
- Contamination: how do we test whether a benchmark is measuring capability or recall? Perturbation studies
  (rename entities, change constants) as a cheap contamination probe.
- Is there a benchmark for *knowing when to stop*? Over-eagerness and premature handoff are the two failure
  modes most visible in practice and least represented in scores.

## Notes and memory as experimental objects
- Does handoff-note *format* change downstream agent accuracy? Fix a task, have A write a note under
  format F, have B continue from the note alone, sweep F. See `2026-08-29-benchmark-vs-instrument.md`.
- Hypothesis: recording **rejected alternatives** is the highest-value part of a note, because it is
  what prevents a re-derivation loop — and it is what every summarizer drops first. Compaction is lossy
  in a biased direction: it keeps conclusions and discards the search that produced them.
- Does an agent reading a note reconstruct the *reasoning* or only the *conclusion*? Testable by asking
  the reader to defend the decision against the counterargument that was originally raised against it.
- Is there an optimal note length, or does it depend on how far downstream the reader is?
- Does rhetorical confidence lower a reader agent's rate of catching a false claim, at equal
  information content? If so, style is a safety property, not taste. See `experiments/002-rhetoric-vs-information/`.

## Speculative / cross-domain
- Agent workflows as a scheduling problem: does anything from operations research (critical path, queueing)
  predict where multi-agent pipelines stall?
- Economics framing: an agent pipeline is a firm making make-vs-buy decisions per subtask. Does the
  transaction-cost account of firm boundaries predict where agent boundaries should fall?
- PIC analogy: multi-agent systems as particles in a shared field, where the field is the shared context.
  Probably a stretch, but the "long-range vs. local interaction" split maps onto shared-context vs. handoff designs.

## Where on the prompt axis is a configuration sweep sitting? (2026-08-30)

001 found the prompt axis (0.27–0.72) is three times wider than the configuration axis
(0.51–0.63) on the same model and tasks, and its best point is also its cheapest. See
[`2026-08-30-prompt-dominates-configuration.md`](2026-08-30-prompt-dominates-configuration.md).

Open:

- Does the ensembling gain survive at the top of the prompt axis, or was it compensating for
  a bad prompt? Re-running the C curve on the B1n prompt answers this and is queued.
- Is "find the prompt ceiling first" tractable in general, or does it just move the search
  cost around? Finding the ceiling took three tries here, two of which produced confounded
  arms that scored plausibly.
- Does the one-context/k-context asymmetry hold on a task with separable subgoals, where
  seeing another derivation carries information rather than just a prior?

## Panel composition decided every outcome in 001 vs 003 (2026-08-30)

Two experiments, identical tasks, identical voting rule, identical revision prompt; only the
membership differed. Composition flipped the sign of the agreement–correctness relationship
(unanimity 0.78 vs 0.31), decided whether voting helped or hurt (+0.07 vs −0.08 against the
best member), and decided whether deliberation did anything (nothing vs +0.13 to the weakest
member). See [`2026-08-30-who-is-in-the-room.md`](2026-08-30-who-is-in-the-room.md).

Open:

- Does a panel where the strong side is not outvoted — two members, or a vote weighted by solo
  accuracy — capture the capability transfer that 003's 2-against-1 threw away?
- Is willingness to adopt a peer answer a stable model property? Mistral adopted 56% and gained
  0.13; llama adopted 35% and lost 0.03. One observation each.
- Where is the Condorcet threshold once every member is prompted at its ceiling rather than
  0.21 below it? All of 003's solo rates were measured on the bare prompt.
