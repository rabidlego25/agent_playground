# 007 capability screen — observed facts

> **Three runs, 2026-09-10.** Run 1 (12-cell pool) 7/7 clean = 1.00. Run 2 (parameterised
> pool, broken pacer) 3/3 clean, 7 of 10 lost to 429s. Run 3 (parameterised pool, corrected
> pacer) **9/10 = 0.90, 0 rate-limited**. Run 4, 2026-09-11 (multi-edit defects, n=20)
> **15/20 = 0.75, FUNDABLE** — and multi-edit defects turned out *easier*. Sections below
> are written against run 1 unless marked; later runs are appended at the end.

**Date:** 2026-09-10. **OpenClaw 2026.9.3**, image `openclaw-007`. Backend: Google AI Studio
free tier, `gemini-3.5-flash-lite` via the OpenAI-compatibility endpoint. Arm A only, n=10,
82 requests spent.

Not a finding about agents. This is the check the README requires before three arms run —
"do not run the main comparison until every arm's base rate is off the floor" — and its
headline is that **the floor was never the risk; the ceiling is.**

## Result

```
  raw          7/10 = 0.70   (counts 429 aborts as failures)
  clean        7/7  = 1.00   Wilson95 [0.65, 1.00]
  rate-limited 3/10
  worked the task and got it wrong: 0
  -> CEILING (>0.85). Harden the 12-defect pool before running three arms.
```

Against the rule committed in `screen.py` before the run (<0.25 floor, >0.85 ceiling), this
is a ceiling. **Every instance that ran to completion passed.** Not one instance exists where
the agent worked the task and got it wrong.

The raw 0.70 is meaningless and nearly caused the opposite conclusion. All three failures are
429 aborts at 1–3 calls and 4–8s wall time — the agent never edited anything. A 429 abort is a
harness event; counting it as a capability failure put the number in the fundable band and
inverted the verdict. `_verdict()` now reports the clean rate and the raw rate separately, and
counts "worked the task and got it wrong" explicitly, because that count is the one that
distinguishes a hard task from a broken harness.

## The binding quota is input tokens per minute, not requests

Read off the 429 body:

```
quotaId     GenerateContentInputTokensPerModelPerMinute-FreeTier
quotaValue  250000
retryDelay  49s
```

This corrects the reasoning that chose this backend. The argument was that Flash Lite's
250K TPM meant TPM could never bind, RPM would, and 429s would therefore be avoidable by
pacing on requests. Wrong: an agent loop resends the whole conversation every turn, so input
tokens grow with turn count and the per-minute cap is reached by a few concurrent instances.

Measured over the 7 completed instances:

| | |
|---|---|
| input tokens per instance | 60,643 mean |
| input tokens per call | 5,513 mean |
| calls per instance | 10–12 |
| peak observed rate | 215,847 input tok/min |

One instance alone costs ~24% of the per-minute budget. Three inside one minute breach it,
which is exactly what happened. Pacing on request count does not bound this.

**What this means for arm B, and it is the number that decides the design.** PILOT.md measured
arm B at 30–60+ turns per instance. At 5,513 input tokens per call that is **165K–330K input
tokens for a single instance** — up to 1.3× the entire per-minute cap for one instance of one
arm. Arm B cannot run inside a minute's budget and must be paced across several.

This is not the Groq failure repeating, and the distinction is the whole reason this backend
is still viable. On Groq a single turn (16.7k) exceeded the entire per-minute budget (8k), so
no pacing could make one turn fit. Here a turn is 5,513 against 250,000 — it fits 45× over.
The cap is reached by *aggregation*, which pacing controls, rather than by the *unit of work*,
which it cannot. So 429s are avoidable here and were not avoidable there. But only if the
harness actually paces, which the first run did not.

## OpenClaw aborts on 429 rather than backing off

`stopReason: "error"`, `aborted: false`, run over in 4s, despite Google supplying
`retryDelay: 49s`. The retry machinery in the package (`retryAfterMs`, `maxAttempts`,
`shouldRetry`) did not engage on this path. No provider-level retry knob was found in the
config type.

Handled in the harness instead: `screen.py` paces on a trailing-60s input-token window to a
175K target (70% of cap) and retries a rate-limited instance up to twice. A 429 aborts before
the agent edits anything, so the retry starts from a clean workspace — verified, and the
workspace is rebuilt rather than assumed clean.

## Detecting a rate limit: read the trace, not stderr

The first run flagged rate limiting with a stderr grep and got 4/10, including a **false
positive** on `repair-intervals-707`, which completed 12 calls and passed. The trace is
authoritative: `export.rate_limit_error()` scans the serialized trajectory event and returns
the quotaId. It gives 3/10, and those three are exactly the three failures.

One trap inside that: `errorMessage` is nested inside the message snapshot, not at the top of
`data`. Reading only the top level returns "no rate limit" for a run that died of one.

## What is still unpinned

Unchanged from PILOT.md, and neither is reachable without running arm B:

- whether `--model-map` holds one model across all nine agents;
- whether an inter-agent message appears as a `content[].toolCall` with a name in
  `AGENT_TO_AGENT_TOOLS`. The shape is now a concrete guess rather than an unknown, but it is
  still a guess, and **H3 is not computable until it is confirmed.**

## Cost

82 requests and ~430K input tokens, inside the free tier. No money spent; the project is
unbilled. No result about agent configurations claimed, and none implied — this is arm A on
ten instances of a twelve-defect pool.


---

# Run 3 — corrected pacing, parameterised pool (2026-09-10)

```
raw / clean   9/10 = 0.90   Wilson95 [0.60, 0.98]
rate-limited  0/10          108 requests
worked the task and got it wrong: 0
-> CEILING (>0.85)
```

## The pacer was budgeting on the wrong number

Run 2 lost 7 of 10 instances to 429s *with pacing enabled*, which is worse than run 1 with
no pacing at all. Two causes, both mine:

- **`cacheRead` is ~16,200 of the ~21,000 tokens per call** — the system prompt and tool
  schemas — and Google's input-token quota counts the cached prefix. `totalTokens = input +
  output + cacheRead`. The pacer budgeted on `input` alone, which reports ~5,000, so it
  under-counted by 3–4× and believed it had headroom while sitting on the cap. **One
  10-call instance is 217K–246K against a 250,000/min cap: 87–98% of a minute's quota on
  its own.**
- **Retries ignored `retryDelay`.** Each 429 carried 30–59s; the retry fired immediately
  and bought another 429, two wasted requests per instance.

Corrected: pace on `quota_tokens()`, honour the supplied delay. Run 3 paced ~61s between
instances and lost nothing.

This also corrects the arithmetic that justified this backend. A call is ~21,000 tokens,
not the ~5,500 the `input` field suggested. **Arm B at 30–60 calls is 630K–1,260K per
instance — 2.5–5 minutes of quota for one instance of one arm.**

`--local-model-lean` cuts a call to 8,708 tokens (`cacheRead` → 0), a 2.4× reduction, and
an instance still passed 11/11 under it. It is a real lever and an open decision: arm B is
pre-registered as "installed as shipped", so imposing a reduced tool surface on it changes
the treatment even though applying it uniformly keeps the arms matched.

## Parameterisation moved the pool, and it was not enough

1.00 → 0.90. The single failure is not a wrong fix: the agent wrote a `test_intervals.py`
and never edited `intervals.py`, spending its turns on tests. A real agent failure mode,
and one worth measuring across configurations — but still **zero instances where an agent
edited the module and got it wrong.**

## The real blocker is n, not difficulty

Power at 0.05, paired McNemar, effects the size 004/006 measured (+0.15 ensembling,
−0.20 deliberation), rho=0.3 for shared instance difficulty:

| n | C>A (.80 vs .65) | A>B (.65 vs .45) |
|---|---|---|
| 40 | 0.14 | 0.22 |
| 80 | 0.33 | 0.46 |
| 160 | 0.65 | 0.81 |
| 240 | 0.84 | 0.95 |

**n=40 has 14–22% power.** It was chosen as "what the budget allows" and never checked
against an effect size. Worse, at A=0.90 the C>A leg is unreachable at *any* n that fits
the budget: even a perfect arm C gives p=0.125 at n=40, because only 0.10 of headroom
exists above arm A.

So two things must both change before the main run, and they trade against each other:

- **difficulty** — arm A wants to land near 0.60–0.70, to leave headroom on both sides;
- **n** — 160+ for either leg to be worth reporting, against ~11 calls/instance, 500 RPD,
  and three arms.

n=160 × 3 arms × ~11 calls ≈ 5,300 requests ≈ 11 days of free-tier quota. That is the
honest cost of a result 007 could publish, and it is a different design from the one
pre-registered.


---

# Run 4 — multi-edit defects, n=20 (2026-09-11)

```
raw / clean   15/20 = 0.75   Wilson95 [0.53, 0.89]
rate-limited  0/20           232 requests
worked the task and got it wrong: 1
-> FUNDABLE (0.25-0.85)
```

Arm A is off the ceiling and inside the band the amended design needs. The pacer held for a
second run: 0/20 rate-limited, ~61s between instances, 217K–248K quota tokens each.

## The hardening worked, for the opposite reason to the one intended

| defect | passed |
|---|---|
| 1-edit | 6/11 = 0.55 |
| 2-edit | **9/9 = 1.00** |

Fisher exact, one-sided, **p = 0.0298**. Multi-edit defects are *easier*. The pool got
harder only because raising `MULTI_EDIT_RATE` to 0.6 also pushed a lot of draws through
operators that happened to be subtle — not because multi-edit is hard.

They are genuinely multi-edit: generation reverts each edit in turn and rejects the operator
unless the module still fails with any one undone, and the probe confirms it through the
real oracle (74 partial fixes, 0 wrongly passed). They are real, and they are easier.

**Mechanism.** All five failures left `test_*.py` behind — `test_more.py`,
`test_comprehensive.py`, `test_bug.py`. The agent probes before fixing. A two-edit defect
breaks more behaviour in more places and is found on the first probe; a quiet one-line error
survives it. The four operators that failed every draw are all quiet and local:
`covered-fencepost` (`end - start` → `end - start + 1` inside a sum), `no-count` (a counter
that stops incrementing), `no-start-check` (a dropped guard), `off-grid` (`<` → `<=` in a
bounds check).

`discriminating` — how many hidden cases the mutant breaks — does *not* separate pass from
fail either (failures 2–9, passes 6–9). What matters is whether the *agent's own* tests
cover the broken case, not whether ours do.

Written up in `notes/2026-09-11-defect-detectability-not-edit-count.md`.

## Consequence

`MULTI_EDIT_RATE` cut 0.6 → 0.2, predicting 0.2 × 1.00 + 0.8 × 0.55 = **0.64**, inside the
0.60–0.70 target. That prediction is derived from the same n=20 that produced the finding,
so it is a prediction and not a result — seeds 720–739 are held out to check it.

Four of five failures were `untouched`: the agent wrote probe tests and never edited the
module. Only one instance edited and still failed. That failure mode is worth carrying into
the main run as its own column, since it is exactly the kind of thing a Planner/Coder split
might change — and it is the tool-using analogue of the `format_ok` distinction 001 needed.


---

# Run 5 — held-out validation, seeds 720–739 (2026-09-11)

**Written before the run.** Run 4 chose `MULTI_EDIT_RATE = 0.2` using the same n=20 that
produced the 1-edit/2-edit split, so its 0.64 is a prediction fitted on its own data. Seeds
720–739 were reserved for exactly this check and have never been run.

## The prediction, committed before any request

Run 4 measured 1-edit **0.55** (6/11) and 2-edit **1.00** (9/9). The held-out draw is
generated and inspected locally — free, no API — and its realised mixture is **13 one-edit,
7 two-edit**, not the nominal 20%:

| | design-level | this draw |
|---|---|---|
| 2-edit share | 0.20 | 0.35 |
| predicted pass rate | 0.64 | **0.71** |
| predicted passes / 20 | 12.8 | **14.2** |

**The number to judge is 0.71**, because it conditions on the mixture that will actually be
run. 0.64 is what the rate implies in expectation over draws and is not what these 20 seeds
are. Recording both, so neither can be chosen after the fact.

- **Validated** if the clean rate lands in 0.60–0.85 — off the ceiling, inside the band the
  amended design needs, and consistent with the split run 4 measured.
- **Run 4's split does not transfer** if the rate lands above 0.85 (back to a ceiling) or
  below 0.55. Either way `MULTI_EDIT_RATE` was tuned on noise and the pool needs a different
  lever.
- Wilson95 on n=20 is roughly ±0.20, so this cannot resolve 0.64 from 0.71. It can resolve
  *ceiling* from *fundable*, which is the decision the pool needs to support.

Secondary, and the reason run 4 flagged it: **`untouched` vs `edited, still failing`.** Run 4
had 4 untouched of 5 failures. If that ratio holds, the dominant arm A failure mode is an
agent that probes with `test_*.py` and never edits — carried into the main run as its own
column.

## Budget

~240 requests at ~12 calls/instance. Run 4 spent 232 earlier the same Pacific day against a
500 RPD cap, so this sweep is capped at 260 and may stop short; a partial n is reported as
partial rather than topped up from a second day's quota, since instances would then differ in
nothing that matters but would no longer be one draw.

## Result — the prediction failed, and the pool was never hardened

```
raw / clean   19/20 = 0.95   Wilson95 [0.76, 0.99]
rate-limited  0/20           219 requests
predicted     0.71 (14.2/20) committed above, before the run
-> CEILING (>0.85)
```

**Predicted 14 passes, got 19.** Against the bands committed above this is the "run 4's split
does not transfer" branch: `MULTI_EDIT_RATE` was tuned on noise.

The 1-edit rate is where it breaks, and it is the comparison run 4's whole story rested on:

| | run 4 (700–719) | run 5 (720–739) |
|---|---|---|
| 1-edit | 6/11 = **0.55** | 12/13 = **0.92** |
| 2-edit | 9/9 = 1.00 | 7/7 = 1.00 |
| overall | 15/20 = 0.75 | 19/20 = 0.95 |

Fisher two-sided: overall p=0.182, 1-edit p=0.061. Run 5 shows **no 1-edit/2-edit gap at all**
(12/13 vs 7/7). The p=0.0298 that justified cutting the rate to 0.2 did not reproduce, and
`notes/2026-09-11-defect-detectability-not-edit-count.md` is retracted at the head.

**Confound, stated because it limits what can be concluded.** Run 4 ran at
`MULTI_EDIT_RATE=0.6` and run 5 at 0.2. That parameter is consumed from the same RNG stream
that picks the operator, so the 1-edit draws in the two runs are not the same population —
this is not a pure seed replication. What *is* clean is the headline: 0.95 is the held-out
measurement of the configuration as it currently ships.

## The four screens are all one number

| run | n | rate |
|---|---|---|
| 1 | 7 | 1.00 |
| 3 | 10 | 0.90 |
| 4 | 20 | 0.75 |
| 5 | 20 | 0.95 |

Pooled **50/57 = 0.88**, and every run is inside binomial noise of it (run 4, the outlier, at
p≈0.06). Nothing done to the pool across four rounds of "hardening" has moved arm A off ~0.9.
Run 4 read a low draw as a hardening effect and shipped a parameter change on it; run 3 read
1.00 → 0.90 the same way. **n=20 cannot resolve 0.75 from 0.95** — the Wilson intervals
[0.53, 0.89] and [0.76, 0.99] overlap across most of their range — so no screen at this n can
tune a difficulty knob, only detect a floor.

## Consequence for the design

Arm A at ~0.9 leaves 0.1 of headroom, so **the C>A leg is unreachable at any n the budget
allows** — the point run 3 already made, now with the pool "hardened" twice since. The lever
has to change the task, not its parameters: a longer dependency chain, a defect whose
specification is ambiguous without reading the hidden cases, or an oracle the agent's own
probing cannot approximate. Picking one on a 20-instance screen is what produced this, so the
next calibration needs n≥60 or a decision rule that does not depend on separating 0.75 from
0.95.

The harness itself is fine: 0/20 rate-limited for a third consecutive run, 219 requests,
13–18s per instance. Nothing here is a backend problem.
