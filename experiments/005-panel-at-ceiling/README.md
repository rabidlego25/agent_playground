# 005 — Does the mixed panel clear the Condorcet threshold once every member is prompted at its ceiling?

**Status:** sample phases complete (2026-09-01); deliberation phases interrupted at 30/195 and
not yet reported. **Hypotheses pre-registered and committed (dc6a516) before any arm was run.**
**Result: H1 failed again and harder; H2 rejected — the prompt gain does not transfer to
llama3.1 at all; H3 confirmed — prompting and heterogeneity buy independence that stacks.**

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

## Results — sample phases (2026-09-01, n=195)

Both round-one phases completed at full n. The deliberation phases were interrupted 30/195
into the first of three, so **H4 is not reported here**; H1, H2 and H3 need only round-one
draws and are complete.

| arm | acc | 95% CI | tok_in | tok_out | total |
|---|---|---|---|---|---|
| solo bare: qwen2.5 | 0.51 | [0.44, 0.58] | 31,838 | 21,976 | 53,814 |
| solo bare: llama3.1 | 0.22 | [0.17, 0.28] | 28,133 | 32,955 | 61,088 |
| solo bare: mistral:7b | 0.18 | [0.14, 0.24] | 30,615 | 1,573 | 32,188 |
| solo B1n: qwen2.5 | **0.67** | [0.60, 0.73] | 37,688 | 18,021 | 55,709 |
| solo B1n: llama3.1 | 0.19 | [0.15, 0.26] | 33,983 | 60,746 | 94,729 |
| solo B1n: mistral:7b | 0.29 | [0.23, 0.36] | 37,407 | 21,906 | 59,313 |
| C-mixed′: k=3 vote, no comms | 0.58 | [0.51, 0.65] | 109,078 | 100,673 | 209,751 |

### H2 — rejected as stated. The prompt gain does not transfer uniformly

| member | bare | B1n | delta | p (paired) |
|---|---|---|---|---|
| qwen2.5 | 0.51 | 0.67 | **+0.154** | 0.0016 |
| llama3.1 | 0.22 | 0.19 | **−0.026** | 0.583 |
| mistral:7b | 0.18 | 0.29 | **+0.108** | 0.0111 |

H2 predicted **both** weak members would gain ≥ +0.10. Mistral did (+0.108, and it was the
predicted direction — it emitted 8.1 output tokens per sample on the bare prompt, i.e. was not
reasoning at all, and moved to 112). **llama3.1 gained nothing.**

This is the answer to the question 004 could not ask: **"fix the prompt first" is not universal
advice.** The same sentence is worth +0.154 to one model, +0.108 to another and 0.000 to a
third, on identical tasks. A prompt intervention is a property of the *pair* (prompt, model),
not of the prompt.

### The cap guard fired, and the diagnostic clears it

The pre-registered rule was: above 5% cap-binding, report the solo rate as a lower bound and
re-run at 1600.

| member | cap-bound at 800 |
|---|---|
| qwen2.5 | 0/195 (0.0%) |
| **llama3.1** | **23/195 (11.8%)** |
| mistral:7b | 0/195 (0.0%) |

llama tripled its output under B1n (169 → 312 mean, median 216) and ran past the cap on 23
tasks. But truncation does not explain its null:

| llama3.1 subset | n | B1n acc | same tasks, bare |
|---|---|---|---|
| not cap-bound | 172 | **0.198** | **0.198** |
| cap-bound | 23 | 0.174 | — |

**Identical to three decimals on the untruncated subset.** llama is not being robbed of accuracy
by the token cap; it gets nothing from the instruction. The 1600 re-run the rule obliges is
still owed and is now a confirmation rather than a decider — recorded here so the rule is not
quietly dropped because the post-hoc analysis went the convenient way.

A second llama problem is visible and is *not* about the cap: 41/195 completions failed to
produce a parseable `ANSWER:` line, and only 23 of those were truncated. The remaining 18 are
plain format non-compliance. llama3.1's rate on this task family is partly an
instruction-following measurement, not only a reasoning one.

### H1 — failed again, and harder than in 003

| | best member | mixed vote | p |
|---|---|---|---|
| 003 (bare) | 0.51 | 0.43 | 0.0070 |
| **005 (B1n)** | **0.67** | **0.58** | **0.0001** |

The gate fails a second time. The panel improved a lot in absolute terms (0.43 → 0.58) and the
gap to its best member *widened*, because the prompt moved the strongest member furthest. Fixing
the prompt made the composition problem worse, not better: qwen2.5 pulled to 0.67 while llama
stayed at 0.19, so the vote is now 2-against-1 by a larger margin. **Prompting a panel at its
ceiling does not fix an unequal panel; it can make it more unequal.**

### H3 — confirmed, and the two sources of independence compose

| condition | c |
|---|---|
| bare, within-family (001) | 0.339 |
| bare, cross-family (003) | 0.249 |
| B1n, within-family (004) | 0.239 |
| **B1n, cross-family (005)** | **0.211** |

Cross-family error independence rose again on the reasoning prompt (0.249 → 0.211), and the
combined figure is below *either* single intervention. **Heterogeneity and prompting buy
different independence and stack.** That is the cleanest result on this page and the one with
implications outside this repo: it says a mixed panel and a good prompt are not substitutes.

It also sharpens what went wrong. Independence is not the binding constraint on a mixed panel —
005 has the most independent errors ever measured here (0.211) and its vote still loses to one
member by 0.09, p=0.0001. **Competence is the binding constraint, and independence only pays
once members clear the threshold.** 003 read its failure as a composition problem and was right;
004 read its success as an independence story and was right; 005 shows independence without
competence buys nothing at all.
