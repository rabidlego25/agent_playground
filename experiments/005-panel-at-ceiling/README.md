# 005 — Does the mixed panel clear the Condorcet threshold once every member is prompted at its ceiling?

**Status:** pre-registered 2026-09-01, not yet run.

## Question

003 built a mixed-family panel to falsify 001's error-correlation account and could not test
it, because two of three members sat far below the competence threshold a majority vote needs:
qwen2.5 0.51, llama3.1 0.22, mistral:7b 0.18. The three-way vote landed *below* its best member
(0.43 vs 0.51, p=0.0070).

Every one of those rates was measured on the bare prompt. 004 then showed that prompt is worth
+0.16 to qwen2.5 (0.51 → 0.67) and — the load-bearing part — that a reasoning prompt *raises*
error independence rather than spending it (conditional-on-wrong agreement 0.339 → 0.239).

So 003's failure may have been entirely a prompt artifact. This runs the same panel, same
tasks, same voting rule, same revision wording, changing only the prompt.

## What is already known before the run

Two numbers computed by replay from 001's and 003's existing traces, at zero token cost:

| condition | c = P(a second answer repeats the first \| the first is wrong) |
|---|---|
| bare prompt, within-family (001) | 0.339 |
| bare prompt, **cross-family** (003) | **0.249** |
| B1n prompt, within-family (004) | 0.239 |

**Heterogeneity did buy error independence in 003** — 0.339 → 0.249 — exactly as its H2 argued
it would. It bought nothing usable because the members were too weak to convert independence
into accuracy. And one sentence of prompt bought slightly *more* independence (0.239) than
swapping in two different model families did. That framing is what 005 tests.

Also on the record before the run: **mistral:7b emitted 8.1 output tokens per sample** on the
bare prompt (1,573 across 195 tasks) against llama3.1's 169.0 and qwen2.5's 112.7. It was not
reasoning at all; it was emitting an answer line. A three-call pilot on B1n moved it to 63–98
tokens.

## Hypotheses

- **H1 (gate, and deliberately not load-bearing this time).** The mixed vote beats its best
  member on the reasoning prompt. **Predicted to fail again**, on arithmetic: qwen gained +0.16,
  and llama3.1 and mistral would need +0.28 and +0.32 respectively just to reach 0.5.
  003's design error was that everything downstream depended on this gate passing. Here H2–H4
  are per-member and are measurable whether or not it does. That is the lesson 003 paid for.

- **H2 (the primary question).** The reasoning-prompt gain transfers across families: llama3.1
  and mistral:7b each gain ≥ +0.10 from B1n. *Predicted to hold, and to be largest for
  mistral*, which was not reasoning at all on the bare prompt and therefore has the most to
  gain from being told to. 004 measured the prompt effect on exactly one model; if it is
  qwen-specific, "fix the prompt first" is advice about qwen2.5 and not about agents.

- **H3.** Cross-family error independence rises on the reasoning prompt, as within-family
  independence did: `c′ < 0.249`. Cross-family `c` is the quantity that decides whether a mixed
  panel can help at all, and until this run it has been measured only on the bare prompt.
  *Predicted to hold.* If both prompt and heterogeneity buy independence, the question is
  whether they compose or whether they buy the same independence twice — measurable here as
  whether cross-family `c′` falls below the within-family 0.239.

- **H4.** 003's capability transfer shrinks or vanishes once the weak members have their own
  derivation. In 003 mistral gained **+0.13** purely from reading two peer answers. 004 showed
  that within-family this effect is gone at the ceiling (97 wrong→right against 97 right→wrong,
  net exactly zero, against 001's +36). *Predicted to shrink*, by 004's mechanism: a peer
  answer is informative to an agent that has not worked the chain and noise to one that has.

## Design

n=195, `multi_hop` depth 4, temperature 0.7, seeds 5000–5194 — identical instances to 001, 003
and 004, so every arm pairs against all of them.

Panel and phase structure are 003's, unchanged: one pass per model rather than one per task,
because a 16 GB machine holds two 7–8B models and not three. Peers keep panel order and are
labelled A/B/C, so position cannot be confounded with family.

Neither prompt is retyped. `run.py` loads `B_ONE_N` and `PEER_TEMPLATE` out of
`001-deliberation/run.py`, the same way 004 does, so all four experiments share one wording.

qwen2.5's round-one draw is **reused from 004** (`004_samples.jsonl`, j=0) rather than redrawn —
same weights, same prompt, same seed — exactly as 003 reused 001's. Only llama3.1 and mistral
need new samples. Draw seeds are `seed*10 + 300` (matching 004's samples block); revision seeds
are `seed*10 + 500 + j`, disjoint from 004's revision block (`+400+j`).

**Token cap: 800 for all three members**, identical to 004. Per-model caps would confound model
with cap. llama3.1 is verbose — one pilot completion reached 707 tokens — so the cap-binding
rate is reported per model, with a rule fixed in advance: **if any member binds on more than 5%
of tasks, its solo rate is reported as a lower bound and a diagnostic re-run at 1600 follows.**
A truncated completion loses its `ANSWER:` line and scores as wrong, which would be an
instrument artifact masquerading as a capability result — the same class of mistake as 001's
format-suppression bug.

## What counts as an answer

H2 is the primary and is per-member and paired: each model's B1n draw against its own bare draw
on the same 195 instances, exact McNemar. H1 is a gate on the panel arm only. H3 is a single
number against the 0.249 baseline above. H4 is the wrong→right / right→wrong table from 003,
recomputed.

Cost normalisation follows 003 and 001: the deliberation arm pays for the round-one samples it
reuses.

## Known weaknesses, stated in advance

- One prompt at each end, not a curve. "At its ceiling" means "on the one sentence that worked
  for qwen2.5", which is not established as any other model's ceiling — and if H2 fails, the
  most likely explanation is that B1n is qwen's ceiling and not llama's or mistral's. That
  ambiguity is inherent to the design and cannot be resolved by this run.
- k=1 per family, as in 003. Within-family `c` for llama and mistral is therefore not measured
  here; only the cross-family figure is.
- Same single task family as 001, 003 and 004.
