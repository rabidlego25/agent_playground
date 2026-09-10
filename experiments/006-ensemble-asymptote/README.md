# 006 — Where does the ensembling curve saturate on the reasoning prompt, and does `c` predict it?

**Status:** complete 2026-09-10. Pre-registered 2026-09-01 (commit `b57eac6`); the sweep ran
51/195 on 2026-09-01 and the remaining 144 on 2026-09-10. **Prediction and estimator were fixed
in this file and committed before any draw was taken.** Result: **k=15 = 0.877, inside the
pre-registered band — but the band could not discriminate its own named alternative.**

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

## Result (2026-09-10)

n=195, qwen2.5, B1n, temp 0.7, 15 draws per task (004's seven + eight new). New draws bound the
800-token cap on 0/1560 (0.0%), matching 004's 0/1365. The k≤7 prefix reproduces 004 exactly.

| k | acc | 95% CI | total tokens |
|---|---|---|---|
| 1 | 0.667 | [0.60, 0.73] | 55,709 |
| 3 | 0.738 | [0.67, 0.80] | 166,249 |
| 5 | 0.831 | [0.77, 0.88] | 276,012 |
| 7 | 0.862 | [0.81, 0.90] | 386,371 |
| 9 | 0.851 | [0.79, 0.89] | 496,592 |
| 11 | 0.872 | [0.82, 0.91] | 607,428 |
| **15** | **0.877** | [0.82, 0.92] | 828,464 |

Adjacent-k, paired exact McNemar on the same 195 instances:

| step | | discordant | p |
|---|---|---|---|
| k=1 → 3 | 0.667 → 0.738 | 6 / 20 | **0.0094** |
| k=3 → 5 | 0.738 → 0.831 | 0 / 18 | **<0.0001** |
| k=5 → 7 | 0.831 → 0.862 | 3 / 9 | 0.146 |
| k=7 → 9 | 0.862 → 0.851 | 5 / 3 | 0.727 |
| k=9 → 11 | 0.851 → 0.872 | 2 / 6 | 0.289 |
| k=11 → 15 | 0.872 → 0.877 | 3 / 4 | 1.000 |

### H1 held, and the test was not sharp

k=15 = **0.877** against a pre-registered 0.89 [0.86, 0.93]. Inside the band.

That is a weaker result than it looks, and the weakness is in the pre-registration, not the
data. The named alternative was the plug-in estimator's **0.862** — which is *also inside the
band*. Measured 0.877 sits 0.013 from the prediction and 0.015 from the alternative: a tie. The
run cannot say which estimator was right, so **`c` still has not had a discriminating
out-of-sample test.** The third outcome (>0.93, both estimators biased low) is excluded, which
is the one thing the band did settle.

**Rule for the next pre-registration in this repo: the band must exclude the rival estimator.
A band that contains both predictions cannot be wrong and therefore cannot be informative.**

### Saturation is at k=5, and 004 overstated the gap

The first k after which no later step is significant is **k=5** (5→7 p=0.146, and nothing
after). 004 said the B1n curve "was still climbing at its pre-registered maximum" and concluded
that where the curve saturates is a property of the prompt. With the full curve in hand:

- The claim survives in direction — bare saturates at k=3, B1n at k=5.
- It was overstated in size. One step, not a wide margin. What the prompt moved much further is
  the *level*: 0.63 → 0.877 at the plateau.
- k=7 → 9 is a non-significant *dip* (0.862 → 0.851). 004's k=7 point sat on the high side of a
  plateau it had already reached, which is why it read as still climbing.

### Plurality, not sampling, is now the bottleneck

The correct answer appears in at least one of the 15 draws on **0.979** of tasks. Voting reaches
0.877. **The 0.102 gap is what majority selection discards after sampling has already found the
answer** — larger than anything remaining on the k axis, and it does not shrink by drawing more.
For this task, the next gain is in selection or verification, not in more samples.

Cost says the same: k=15 buys +0.015 over k=7 for 2.1× the tokens (828k vs 386k). k=5 at 276k
tokens is 95% of the accuracy for a third of the spend.

### What this changes

- The recommended pipeline out of 001–005 — fix the prompt, ensemble without communication —
  now has a measured ceiling on this task: **~0.88 for qwen2.5 7B at temp 0.7 on B1n**, against
  a 0.979 oracle ceiling. A 7B local model with a good prompt and five samples is competitive
  here; the remaining 0.10 needs a different mechanism, not a bigger k.
- `c` is not yet validated as a predictive variable. It remains a good description of what
  003/004/005 measured and an untested basis for forecasting.
- The k=9 dip and the 0.979 oracle ceiling both come free from traces that are now on disk;
  neither required a new draw.
