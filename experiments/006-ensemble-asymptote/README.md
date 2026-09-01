# 006 — Where does the ensembling curve saturate on the reasoning prompt, and does `c` predict it?

**Status:** pre-registered 2026-09-01, not yet run. **Prediction and estimator fixed in this
file before any draw was taken.**

## Question

004 measured C′ at k ∈ {1,3,5,7} on the B1n prompt and the curve was still climbing at its
pre-registered maximum:

| k | 1 | 3 | 5 | 7 |
|---|---|---|---|---|
| bare (001/004) | 0.51 | 0.58 | 0.61 | 0.63 |
| **B1n (004)** | **0.67** | **0.74** | **0.83** | **0.86** |

On the bare prompt no adjacent-k step above k=3 was significant, so 001 concluded ensembling
saturates at k=3. On B1n, k=5 and k=7 both still paid. From this 004 concluded that **"where
the ensembling curve saturates is a property of the prompt"**
(`experiments/004-prompt-ceiling/README.md:145`).

That is a comparison in which one side was observed and the other was not. The bare curve's
saturation point was measured; the B1n curve's was asserted from the fact that it had not
arrived yet by k=7. This run observes it.

There are two further reasons it is worth 1.7 h of local compute.

**`c` has never been asked to predict anything.** Conditional-on-wrong agreement — P(a second
answer repeats the first | the first is wrong) — is the explanatory variable underneath 003
("heterogeneity buys independence", 0.339 → 0.249), 004 ("the prompt buys it back", 0.339 →
0.239) and 005 ("they stack", → 0.211). In all three it is measured after the fact and used to
narrate a result. It has never been used to make a number that a later measurement could
contradict. If the independence account is right, the 15 draws' answer distribution constrains
where the vote converges. This run states that number first and then measures it.

**It bounds the pipeline this repo actually recommends.** The working order out of 001–005 is
"fix the prompt, then ensemble without communication, and do not deliberate." That pipeline has
no known ceiling. Whether qwen2.5 asymptotes near 0.95 or flattens at 0.87 is the difference
between "a 7B local model with a good prompt and 15 samples is competitive on this task family"
and "ensembling is spent; the remaining 0.14 needs something else." On a 16 GB machine that is
the practically decisive question.

## Design

n=195, `multi_hop` depth 4, temperature 0.7, seeds 5000–5194 — the same instances as 001, 003,
004 and 005, so every arm pairs against all of them.

**004's seven draws are reused as j=0..6 and eight new draws are taken as j=7..14**, from the
same model, prompt, temperature and 800-token cap, at seeds `seed*10 + 300 + j` — a direct
continuation of 004's own block (it used +300..+306), disjoint from 001's samples (`+j`),
deliberate (`+100+j`) and budget (`+200+…`) blocks and from 005's revision block (`+500+j`).
The fifteen are therefore exchangeable and C′ at any k ≤ 15 is the k-prefix of one sweep, as in
001 and 004.

qwen bound the 800-token cap on 0/1365 draws in 004, so the cap is not a factor here; the new
draws' binding rate is reported anyway.

The prompt is not retyped. `run.py` loads `B_ONE_N` out of `001-deliberation/run.py`, as 004
and 005 do.

## The prediction, and how it was arrived at

Two estimators were computed from 004's existing traces at zero token cost, and they disagree.

**Plug-in plurality.** Take each task's empirical distribution over the 7 draws and ask whether
the correct answer is its plurality. That is what an infinite vote converges to if 7 draws
estimate the distribution well. It gives **0.815** strict, **0.862** with the earliest-tie-break
rule the vote actually uses — i.e. k=7's measured 0.862 *is already* the asymptote and every
step beyond it is noise.

**Bootstrap.** Resample k draws with replacement from each task's 7 and vote. This was going to
be the pre-registered estimator until it was calibrated against ground truth already on disk:

| | predicted | measured | error |
|---|---|---|---|
| from a 3-draw pool → k=5 | 0.710 | 0.831 | **−0.121** |
| from a 3-draw pool → k=7 | 0.715 | 0.862 | **−0.147** |
| from the 7-draw pool → k=7 | 0.785 | 0.862 | −0.077 |

The bootstrap **systematically under-predicts**, because resampling from a small pool cannot
reproduce how concentrated the true answer distribution is — it invents diversity that is not
there. Its raw k=15 number (0.813) is therefore a floor, not a prediction. Correcting by the
+0.077 gap it still shows in-sample at k=7 gives **≈0.89**.

- **H1 (pre-registered).** C′ at k=15 lands at **0.89, band [0.86, 0.93]**.
- **Named alternative.** C′ at k=15 lands at **≤0.87** — the plug-in was right, the curve had
  effectively saturated by k=7, and 004's "saturation is a property of the prompt" is true only
  in the weak sense that B1n saturates later than bare, not higher.
- **Third outcome, and the most interesting.** C′ at k=15 exceeds **0.93**. Both estimators
  underestimate, which would mean the wrong-answer tail is more diffuse than 15 draws reveal
  and `c` computed on small k is a biased description of the independence structure — a
  problem for the way 003, 004 and 005 all use it.

Secondary, not a hypothesis: the **oracle ceiling** — the fraction of tasks where the correct
answer appears in at least one of the 15 draws. Voting cannot exceed it, and the gap between it
and k=15 is what plurality discards that sampling already found.

## What counts as an answer

The k=15 accuracy against the band above. Adjacent-k contrasts are paired exact McNemar on the
same 195 instances, as in 001 and 004; saturation is claimed at the first k where no later step
is significant.

## Known weaknesses, stated in advance

- **One model.** This is qwen2.5's asymptote on B1n, not "the" asymptote. 005 already showed
  the prompt effect is a property of the (prompt, model) pair; there is no reason the
  saturation point would be less model-specific.
- **The estimators are not independent of the data they predict.** Both are computed from the
  same 7 draws that form the k≤7 prefix of the measured curve. The out-of-sample content is
  entirely in draws 8–15; the k≤7 part of the reported curve is a reproduction, not a test.
  (It does reproduce: 0.667 / 0.738 / 0.831 / 0.862 and c=0.239, matching 004 exactly.)
- **Single task family**, as in 001, 003, 004 and 005.
- Temperature is fixed at 0.7. The asymptote is a property of the sampling distribution, so it
  is a temperature result as much as a prompt result, and no temperature sweep is run here.
