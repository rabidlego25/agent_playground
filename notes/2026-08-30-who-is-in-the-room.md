# Consensus means opposite things depending on who is in the room

2026-08-30. From `experiments/001-deliberation/` and `experiments/003-mixed-panel/`, both
n=195 on identical `multi_hop` depth-4 instances, same voting rule, same revision prompt.
The only difference between them is panel composition.

| distinct answers among 3 | 001: three qwen2.5 samples | 003: qwen2.5 + llama3.1 + mistral |
|---|---|---|
| 1 (unanimous) | **0.78** | **0.31** |
| 2 | 0.57 | 0.36 |

Unanimity is a strong correctness signal in one panel and an anti-signal in the other. In a
competent homogeneous panel, agreement means the task was easy. In an unequal panel, it
frequently means two weak members fell into the same wrong attractor and the third was
outvoted.

Nothing about the aggregation changed. Only the membership did.

**Consequence for anything that gates on agreement** — self-consistency confidence,
escalation triggers, "the agents concur so ship it": the mapping from agreement to
correctness is a property of the panel, not of the method, and it has to be measured for
each composition. A threshold calibrated on a homogeneous panel is not merely less accurate
on a mixed one; it points the wrong way.

## The vote can be worse than its best member, and here it was

| | acc | paired vs. qwen2.5 solo |
|---|---|---|
| qwen2.5 solo | 0.51 | — |
| llama3.1 solo | 0.22 | |
| mistral:7b solo | 0.18 | |
| three-way majority vote | **0.43** | **p = 0.0070** |

Condorcet's jury theorem requires members above a competence threshold; below it, adding
voters moves the group away from the answer. This is that branch, with a paired test on it.
It is a known result and this is an unintentional demonstration — 003 was built to test
something else and tripped over it.

**The design error was matching the panel on size.** 7–8B for all three members holds capacity
constant only if capability tracks parameter count across families. It does not: llama3.1 8B
is the largest member and the second weakest. Competence is what governs whether a vote helps,
and size is a poor proxy for it.

## Deliberation transferred capability rather than averaging it

| member | pre → post deliberation | changed answer | of those, adopted a peer's answer |
|---|---|---|---|
| qwen2.5 (strong) | 0.51 → 0.50 | 57% | 59% |
| llama3.1 (weak) | 0.22 → 0.19 | 79% | 35% |
| mistral:7b (weak) | **0.18 → 0.31** | 82% | 56% |

The strong member revised 57% of its answers and finished where it started. It was not
dragged toward the majority despite being outnumbered two to one by models less than half as
accurate. Mistral gained +0.13, most of the way from its own level toward qwen's.

This is the opposite of what a herding account predicts, and it sits oddly beside 001, where
homogeneous deliberation moved answers constantly (50%) and gained nothing. The reconciliation
is that in 001 there was nothing to transfer — three samples from one model have the same
competence, so movement is noise. Here there was a gradient, and it flowed downhill.

The panel could not cash it: two weak members still outvote one strong one, so D-mixed (0.50)
is indistinguishable from qwen2.5 alone (0.51, p=0.820) at 9.5× the tokens. **The mechanism
worked and the aggregation threw it away.** A composition where the strong side is not
outvoted — two members, or a vote weighted by solo accuracy — is the obvious test.

Note which weak model gained. Mistral adopted a peer answer in 56% of its revisions and gained
0.13; llama adopted one in 35% and lost 0.03. Willingness to be moved is what paid, not
weakness. One observation each, so this is a hypothesis, not a result.

## What to hold onto

Composition is a first-class variable in multi-agent work, not a detail of the setup. It
determined the sign of the agreement-correctness relationship, whether voting helped or hurt,
and whether deliberation did anything at all — across two experiments that differed in nothing
else. Reporting a multi-agent result without reporting the members' solo accuracies leaves out
the variable that decided the outcome.

See also [`2026-08-30-prompt-dominates-configuration.md`](2026-08-30-prompt-dominates-configuration.md):
every solo rate above was measured on a bare prompt worth 0.21 less than a reasoning prompt, so
all three members sit well below their ceilings and the threshold question would look different
higher up.
