# Decision: what agent_research starts with

**Date:** 2026-08-29
**Method:** two-round adversarial exchange between two instances of the same model, converged at round 2.

## Rejected: adapter-first, then a cheap-model router

The original plan (build `lib/`, then test whether a local 7B can route tasks to a frontier
model, then test token-matched role decomposition) was rejected on two grounds:

1. **No evaluand.** All three items are transport, not cargo. Nothing can be scored until a task
   set with an oracle exists. On a usage-metered subscription, the task set — not model access —
   is the binding constraint.
2. **The router experiment is circular.** The label "this task needed a frontier call" is *defined*
   by running both tiers on every task, so the pilot spends exactly the savings it aims to
   demonstrate. It only pays off on held-out tasks, which makes it a second-order experiment with a
   generalization claim attached. It belongs later, mined from an existing trace archive.

## Accepted: procedurally generated tasks with programmatic oracles, first

Procedural generation is the move that compounds: contamination resistance for free (fresh
instances per run), a difficulty knob, and unlimited n at zero token cost. It also incidentally
answers the contamination question in `open-questions.md`.

Build order:

1. **`lib/trace.py` — the episode schema.** This is load-bearing and must be right on the first
   commit. The record is an *episode of steps*, never a single `(prompt, answer, verdict)` triple:

   ```
   {run_id, commit_sha, timestamp, task_id, seed, config,
    steps: [{i, state_before, action, observation, tokens, latency}],
    verdict, subgoals_hit}
   ```

   A single-shot puzzle is an episode of length 1. Getting this wrong is the one mistake that
   cannot be cheaply undone: it would structurally encode single-shot tasks, force a schema
   rewrite for every later multi-step family, and make all prior runs incomparable.

2. **`lib/tasks.py` — closed-form families.** Constraint/scheduling puzzles with unique checkable
   answers, short functions with hidden unit tests, seeded multi-hop logic chains.

3. **`lib/models.py` — two backends.** ollama HTTP, and Claude via `claude -p --output-format json`.
   Note the enabler: the Pro subscription is scriptable through print mode, so nothing here is
   blocked on a third-party API key.

4. **`lib/worlds/fs_world.py` — the multi-step family.** Deferred but planned, so the schema above
   is not speculative. See below.

## The multi-step task family (planned, ~200 lines)

A seeded filesystem/CLI micro-world. `generate(seed) -> (tree, task_spec, oracle)` materializes a
synthetic directory tree in a temp dir with planted content. Fixed verb set (`ls`, `cat`, `grep`,
`write`, `rm`). The oracle is a **final-state predicate**, not a string match — hash the tree, or
assert `config.yaml["timeout"] == value_derivable_only_from_log_3`.

The design detail that makes it measure what we care about: the generator plants a **dependency
chain of depth d**, where step *i*'s target is discoverable only from step *i−1*'s observation.
That single knob yields:

- **Error compounding** — accuracy vs. d, directly.
- **Handoff tax** — force a summarize-and-pass at a chosen depth, compare against an uninterrupted
  run at the same d.
- **Premature stopping** — partial credit via subgoals reached gives it a failure signature
  distinct from wrong-answer.
- **Recoverability** — plant one irreversible action (a deletable file).

Runs with zero model calls for the environment itself, is seedable, sandboxed in a temp dir, and
exercises the tool-call plumbing needed anyway.

## Experiment 001: does pre-task communication beat one agent?

The user's standing question, and the first experiment. All arms on local `qwen2.5:7b` (free,
unlimited n), **token- and sample-matched**:

| Arm | Configuration |
|-----|---------------|
| A | single agent, direct |
| B | single agent, extended reasoning, token-matched to D |
| C | k=3 independent samples + selection, **no communication** |
| D | k=3 agents, one round of proposal exchange before committing |
| E | k=3, two rounds (dose-response) |

**C is the load-bearing control and the one usually omitted.** "Communication helps" is supported
only if **D > C at matched tokens**. If D ≈ C, the gain was ensembling — three agents that never
spoke would have done as well. That negative result is more interesting than the positive one.

**Mechanism probe.** Measure semantic variance across the k agents before vs. after exchange.
Hypothesis: communication converges toward truth where an oracle exists, and toward the *modal*
answer where it does not — predicting D > C on puzzles and D < C on open-ended generation. This
subsumes the critic-pass question and makes the "criticism causes blandness" intuition measurable.

Caveat: without an oracle, semantic variance stops being a mechanism probe — it can no longer
distinguish convergence-toward-truth from convergence-toward-the-mode — and becomes the *outcome*.
On open-ended tasks, measure diversity collapse directly (pairwise embedding distance, distinct-n)
and pair it with a paired-comparison judge for quality. The claim there is precisely that
communication buys agreement at the cost of range.

**Budget.** The whole sweep runs locally at ~zero subscription cost. Spend metered tokens only
afterward, on a small confirmation slice via `claude -p`, to check whether the finding survives a
capability jump.
