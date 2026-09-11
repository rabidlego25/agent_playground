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

## Task and benchmark design (2026-09-11)

- ~~Harden a repair pool by making defects span more edits.~~ **Wrong knob, measured in 007:**
  multi-edit defects are *easier* (9/9 vs 6/11 for single-edit, Fisher p=0.0298). The agent writes
  its own probe tests, so a defect that breaks more behaviour is found on the first probe while a
  quiet one-line error survives. **Difficulty is set by detectability under the agent's own
  testing, not by the size of the fix.** See
  [`2026-09-11-defect-detectability-not-edit-count.md`](2026-09-11-defect-detectability-not-edit-count.md).
- Following from that: can detectability be *estimated* without a run — by generating plausible
  ad-hoc tests and measuring whether they cover the broken case? That would make difficulty a
  designable property instead of a measured one.
- The count of hidden cases a mutant breaks (`discriminating`) does **not** predict pass/fail.
  What matters is whether the agent's *own* tests cover the broken case, which is a harder thing
  to measure and the more interesting one.
- **[007]** A multi-agent scaffold advertised as general may be a scripted pipeline for one task
  family. Before using any as a treatment, check: does delegation fire without a named workflow?
  Is the inter-agent tool mentioned in any shipped prompt? Does the shipped config even load on
  the current runtime? All three failed silently for `openclaw-agents`.

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

- ~~Does the ensembling gain survive at the top of the prompt axis, or was it compensating for
  a bad prompt?~~ **[004] Answered 2026-09-01: it survives and grows.** The gain is identical at
  k=3 (+0.072) and larger at k=5/7 (+0.067, +0.082) on the reasoning prompt. The reason is the
  surprise: error independence *rose* (conditional-on-wrong agreement 0.339 → 0.239), so base
  rate and ensembling return moved together. Deliberation on the same prompt went from
  uneconomic to significantly harmful (0.71 vs C′7's 0.86, p<0.0001).
- ~~**[004 opens]** Where does the C′ curve saturate?~~ **[006] Running, 2026-09-01.** k=7 was
  the pre-registered maximum and had not flattened (0.74 → 0.83 → 0.86); the bare-prompt curve
  saturated at k=3. 006 extends the sweep to k=15 and — the reason it is worth doing — states a
  number first: k=15 = 0.89 [0.86, 0.93], against a plug-in estimator that says 0.862, i.e. that
  the curve is already done. It is the first time `c` has been asked to predict rather than
  explain.
- **[004 opens]** Is `c` — conditional-on-wrong agreement — measurable from k=3 draws? If so it
  forecasts the ensembling return and makes "should I ensemble this workload" a cheap
  measurement instead of a full curve. **[006] Partial answer, and it is discouraging:**
  bootstrap-extrapolating the *curve* from a 3-draw pool under-predicts k=5 by 0.121 and k=7 by
  0.147, because a small pool cannot reproduce how concentrated the answer distribution is. The
  cheap-forecast version of this question needs an estimator that is not plug-in resampling.
- **[004 opens]** Does the sign flip hold for other prompt interventions, or is step-by-step
  reasoning special? Few-shot examples plausibly go the other way, by supplying a shared
  template that makes errors *more* correlated.
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
  0.13; llama adopted 35% and lost 0.03. One observation each. **[005] A second observation, but
  not directly comparable:** 005 logs `changed_mind` (answer differs from own round one), not
  "adopted a peer", and it is much higher — mistral 73% (+0.082), llama 79% (−0.015), qwen 49%
  (−0.123). The ordering of *gain* held; the adoption rates are a different metric and should not
  be read against 003's without recomputing one from the other's traces.
- ~~**[005 opens, and it is the sharpest one left]** Does deliberation harm scale with the
  *competence gap* between a member and its peers?~~ **[008] Answered 2026-09-11: it tracks the
  gap, not family mismatch — but the gap is not the cause.** Holding family, prompt, weights and
  temperature fixed and moving only peer accuracy (peers are qwen's own scored draws from
  `004_samples.jsonl`), qwen's delta runs +0.180 / +0.101 / +0.065 / −0.115 / **−0.360** as peer
  accuracy falls 1.00 → 0.15. Monotone (H1), −0.360 at gap −0.47 against 005's cross-family −0.123
  at a comparable gap, 2.9× milder (H2), so family mismatch needs no separate explanation. **The
  decomposition replaces the question:** bucketed by how many peers were correct, the delta is
  identical in all five conditions — 0 correct −0.448, 1 correct −0.011, 2 correct +0.202 — and
  only the shares move (0-correct 0% → 81%). Those three constants plus each condition's P(k)
  reproduce every aggregate delta to within 0.022, inside the 0.050 noise floor: competence acts
  *only* through P(zero correct peers). See
  [`2026-09-11-one-correct-peer-is-enough.md`](2026-09-11-one-correct-peer-is-enough.md).

- **[004] retired outright by 008's H3.** 004's "peer answers are informative to an agent that
  has not worked the chain and noise to one that has" is false as stated. With both peers correct
  the subject gains **+0.180** (38 wrong→right against 13 right→wrong). Peer answers carry
  capability; 004 saw net zero because at peers ≈ 0.69 the helpful and neutral blocks cancel.
- ~~**[008 opens, and it is now the sharpest one]** If one correct peer is enough, the
  composition statistic that matters is max(member accuracy), not mean.~~ **[009] Answered
  2026-09-11: no, and the premise was wrong.** One correct peer is not enough — one of three
  is −0.132. Holding max fixed at 1.00 and moving mean 0.33 → 0.67 is worth +0.209
  (p=0.0002). The variable is the **fraction** of peers correct; 008 could not see it because
  all five of its conditions used two peers. One curve fits both experiments, eight
  conditions, leave-one-out max residual 0.034. See
  [`2026-09-11-fraction-not-count.md`](2026-09-11-fraction-not-count.md).
- **[010] The deliberation line has a deployable rule, 2026-09-11.** Deliberate only when
  every peer disagrees with you: +0.101 over always-deliberate, held out on two prompts. It
  works because deliberation is +0.481 when the agent was wrong and −0.287 when it was right,
  and P(wrong | all peers agree) = 0.032. See
  [`2026-09-11-deliberate-only-when-peers-disagree.md`](2026-09-11-deliberate-only-when-peers-disagree.md).
- **[010 opens]** Agreement predicts correctness because wrong answers are diverse and right
  ones concentrate — it survives even in 008/009's selected blocks (AUC 0.810), so it is not
  task-difficulty clustering. That predicts the signal **weakens on tasks with few plausible
  wrong answers**: binary or small-label tasks should break the gate. Directly testable and
  untested.
- **[010 opens]** At larger blocks, is the right cut unanimity or a proportion? Two peers
  cannot say. The 5-peer condition 009 wanted would answer this and the fraction-vs-margin
  question in one run.
- **[009 opens, and it is now the sharpest one]** Fraction correct and *margin* (correct
  minus wrong) order every cell in 008 and 009 identically, so neither experiment can
  separate them. A 5-peer block does: fraction 2/5 and margin −1 pull apart. The fraction
  model was found post hoc and deserves one pre-registered test at a block size neither
  experiment used.
- **[009 opens]** Does the curve cross zero at fraction 0.5 for any subject, or does the
  crossing move with the subject's own competence? 009 has one subject at 0.647. A subject
  well above or below its peers should cross somewhere else if the mechanism is evidential
  rather than social.
- **[008 opens, sharpened by 009]** Is the curve about the fraction *correct*, or the
  fraction that *agrees with the subject's own answer*? 008 cannot separate them — a correct peer usually agrees with a correct
  subject. Constructing blocks where a peer is wrong *but* matches the subject's wrong answer
  would split the two, and it is assemblable from draws already on disk.
- **[008 opens]** Peers in 008 are weak *samples* of a competent model, not a weaker model. Do
  genuinely weaker models err in a way that changes the step function, or only its frequency?
  005's traces hold llama and mistral draws for exactly this comparison.

- **[004] partly retired:** "a composition where the strong side is not outvoted would capture
  the capability transfer" assumes there is transfer to capture. On the reasoning prompt there
  is none — deliberation produced 97 wrong→right against 97 right→wrong, net exactly zero,
  against 001's +36. A peer answer is informative to an agent that has not worked the chain and
  noise to one that has. Whether 003's +0.13 for mistral survives its own prompt fix is the
  open part.
