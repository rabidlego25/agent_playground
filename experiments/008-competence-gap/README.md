# 008 — Does deliberation harm scale with the competence gap, or with family mismatch?

**Status:** H2 answered 2026-09-11 (P65 + P15, n=139); H1 and H3 pending P100/P40/P80.

> **Result: delta +0.065 at gap 0.00, −0.360 at gap −0.47.** McNemar discordant 68/9,
> p<1e−6. H2 lands on the gap-driven branch, and 005's cross-family −0.123 at a similar gap
> is 2.9× smaller — family mismatch is not needed to explain deliberation harm.
>
> **The decomposition matters more than the headline.** Bucketed by how many peers were
> correct, the delta is the same in both conditions (0 correct ≈ −0.44, 1 correct ≈ −0.04,
> 2 correct ≈ +0.27) and only the *shares* move (0-correct: 10% → 81%). The causal variable
> is the number of correct peers, not the gap; competence matters only because it sets
> P(zero correct). One correct peer is enough to stop the damage. See
> `notes/2026-09-11-one-correct-peer-is-enough.md`. **Created:** 2026-09-11. **Predictions committed in this file
before any revision call was made.**

## Question

005 left this as the sharpest open question in the repo, and it is the one 007 was the
expensive way of approaching. Two observations of qwen2.5 deliberating:

| peers | gap below qwen | qwen's delta | source |
|---|---|---|---|
| qwen2.5, same prompt | 0.00 | **net exactly 0** (97 wrong→right vs 97 right→wrong) | 004 |
| llama3.1 + mistral, same prompt | 0.43 | **−0.123** | 005 |

Two points, and the second changes *two* things at once: the peers got worse **and** they
changed model family. So "deliberation harm tracks the competence gap" and "deliberation
harm tracks family mismatch" are not separated by anything on disk.

This separates them by holding family fixed and moving only the gap.

## Design

**The peers are qwen's own real draws.** `004_samples.jsonl` holds 7 independent qwen2.5
draws per task at prompt B1n, each with its full reasoning text and a scored answer. Peer
competence therefore becomes a *knob*: to build a peer at accuracy p, select a correct or
incorrect draw of that same task. Peer answers are real model outputs with real reasoning
and real errors — nothing is fabricated — and every peer is the same model, same prompt,
same weights, same temperature as the subject.

- **Task set: 139.** The tasks where draws 1–6 contain both a correct and an incorrect
  draw, so peer accuracy is dialable from 0 to 1 on *every* task in the set. This drops 56
  of 195 and is a real restriction: it removes the tasks qwen always gets right and the
  ones it never does, so the set is harder than the full pool. Subject solo accuracy on
  it is **0.647** (against 0.692 on all 195). Stated, not hidden — every condition runs on
  the same 139 tasks, so the comparison across conditions is internally valid.
- **Subject: qwen2.5 at B1n, round one reused from `004_samples.jsonl` draw 0.** Not
  re-run. Same weights, same seed, exactly as 005 reused 004's draw and 003 reused 001's.
- **Peers: 2 per task**, drawn from draws 1–6 of the same task, matching the 2-peer
  structure qwen faced in 003 and 005.
- **Revision: `PEER_TEMPLATE` loaded from 001**, the identical wording used by 003, 004
  and 005. Loaded, not copied, so the four cannot drift apart.

**Because the subject's round-one answer is identical in every condition, the only thing
that varies is peer competence.** Conditions are paired on task, so every comparison is
within-subject and exact McNemar applies.

### Conditions

| condition | peer accuracy | gap vs subject (0.647) |
|---|---|---|
| P100 | 1.00 | +0.35 (peers strictly better) |
| P80 | 0.80 | +0.15 |
| P65 | 0.65 | 0.00 (the 004 replication point) |
| P40 | 0.40 | −0.25 |
| P15 | 0.15 | −0.50 (past 005's −0.43) |

695 revision calls, local `ollama`, ~92 min at the 7.9s/call measured from 005. No API
quota, no money.

## The predictions, committed before any run

- **H1 (monotonicity).** qwen's delta — post-revision accuracy minus its own round-one
  accuracy on the same 139 tasks — **declines monotonically** as peer accuracy falls from
  P100 to P15.
- **H2 (the discriminating one).** At **P15**, whose gap (−0.50) exceeds 005's cross-family
  gap (−0.43), the delta is **≤ −0.10** — i.e. at least as harmful as 005's −0.123.
  - If it is, **harm tracks the competence gap**, and 005's cross-family result needs no
    family-specific explanation.
  - If the delta at P15 is materially smaller in magnitude — call it **> −0.05** — then a
    same-family panel of equally incompetent peers is *not* as harmful as a cross-family
    one, and **family mismatch is doing work the gap does not explain.**
  - This is the prediction the experiment exists to settle, and the two branches call for
    different write-ups. Both are recorded here in advance.
- **H3 (transfer).** At **P100**, where every peer is correct, the delta is **positive and
  ≥ +0.10**. 004 found net exactly zero at gap 0 and concluded "a peer answer is
  informative to an agent that has not worked the chain and noise to one that has". If
  P100 is also ≈ 0, that conclusion is stronger than 004 could show: peer answers are
  noise *even when they are right*, and deliberation is not a channel for capability at
  all.

**What would falsify H1:** a non-monotone curve, in particular P40 or P15 landing *above*
P65. That would mean the gap is not the axis and something else — peer confidence,
answer diversity, or agreement pressure — is driving the revision.

## Measures

Per condition, per task: subject's round-one answer and correctness (constant across
conditions), the two peer answers and their correctness, the revised answer, whether the
subject changed its mind, and whether it adopted a peer's exact answer.

**`changed_mind` and `adopted_peer` are recorded separately.** 005 logged only the first
and could not be compared against 003's adoption rates without recomputing one from the
other's traces; that is fixed here rather than repeated.

Reported per condition: delta with Wilson interval, exact McNemar against the P65 anchor
with the discordant-pair counts, adoption rate, and the wrong→right / right→wrong split
that made 004's "net exactly zero" interpretable.

## Known weaknesses, stated in advance

- **One model, one task family, depth 4.** The same limitation every experiment here has
  had since 001. 008 adds nothing on that axis and does not claim to.
- **The 139-task restriction makes the set harder than the pool** and removes exactly the
  tasks where deliberation has least room to act. Generalising the delta magnitudes to the
  full pool is not supported; the *ordering across conditions* is what this measures.
- **Peers are draws of the same model at the same temperature**, so their errors are
  correlated with the subject's in a way independent peers from another family would not
  be. That is the point — it isolates the gap — but it means P15 is not a simulation of a
  weak *model*, it is a weak *sample*. A genuinely weaker model may err differently.
- **Peer accuracy is achieved by selection**, which conditions on correctness. Within a
  task the selected draws are still real outputs, but across the set the wrong answers at
  low p come disproportionately from tasks with many wrong draws — i.e. harder tasks.
  Reported: the per-condition distribution of how many distinct wrong answers existed to
  choose from.
- **n=139, one run per condition.** `probe_variance_floor.py` put run-to-run noise at
  0.050 on single calls, which is the floor any delta here has to clear.
