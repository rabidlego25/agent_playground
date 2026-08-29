# Open questions

Running list. Add freely; mark ones that become experiments with their experiment id.

## Configuration
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

## Speculative / cross-domain
- Agent workflows as a scheduling problem: does anything from operations research (critical path, queueing)
  predict where multi-agent pipelines stall?
- Economics framing: an agent pipeline is a firm making make-vs-buy decisions per subtask. Does the
  transaction-cost account of firm boundaries predict where agent boundaries should fall?
- PIC analogy: multi-agent systems as particles in a shared field, where the field is the shared context.
  Probably a stretch, but the "long-range vs. local interaction" split maps onto shared-context vs. handoff designs.
