# 007 capability screen — observed facts

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
