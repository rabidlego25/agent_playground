# The oracle was measuring instruction-following

**Date:** 2026-08-29. Found while running the first lab probes; traces in `results/confounded/`.

## What happened

The first depth-curve run had llama3.1 at **2/30 on depth-1 lookups** — a single hop, which is
not a task a 8B model fails 93% of the time. The traces said why:

```
"Let's follow the reporting chain upward from Talos:
 Talos reports to Altair. ...
 So, the person 1 level above Talos is Altair."      -> scored WRONG
```

The answer is correct. The oracle took the last line verbatim (`_tail_token`) and compared it to
the gold name, so a model that narrates its conclusion scored zero on every item it got right.
qwen2.5 happened to reply with a bare name and scored normally.

**The comparison was measuring format compliance and reporting it as reasoning.** Left alone it
would have produced a clean, tight-CI, entirely fake headline: "qwen2.5 vastly outperforms
llama3.1 on multi-hop reasoning."

## Why this is the dangerous class of bug

Nothing about the output looked broken. A six-point table with Wilson intervals is exactly as
convincing when the oracle is wrong as when it is right. There was no exception, no warning, and
the numbers were plausible — llama3.1 *being* worse is a believable result. The only reason it was
caught is that 2/30 at depth 1 is implausible on its face, and the raw responses were in the trace
to check. **This is the argument for storing full responses, not just verdicts.**

## The fix

Tasks now request a delimited final line, `ANSWER: <name>`. Scoring is:

1. **strict** — an `ANSWER:` field whose value is a valid candidate → `format_ok = True`
2. **lenient** — otherwise the last valid candidate named anywhere → `format_ok = False`

`format_ok` is recorded per response and reported as its own column, because instruction-following
is a real and model-dependent difference that deserves measuring rather than silently absorbing
into an accuracy number.

## Two fixes tried and rejected (do not reinvent)

- **Last-line verbatim.** The original. Fails on narration.
- **"Take the candidate after the final `is`/`answer` marker."** Fails on answer-first phrasing:
  *"Sable is one level above Quill"* extracts `Quill`. Strictly worse than what it replaced,
  because the failure is silent and favors whichever phrasing the reference model happens to use.

Known remaining limitation: in lenient mode, a response naming the right entity early and
committing to a non-candidate later can score as correct. Recorded rather than papered over —
this is what the `fmt` column is for.

## Consequences

- Any cross-model result from this repo must report the compliance column beside accuracy. A model
  comparison without it is not interpretable.
- Prompt format changes throughput enormously: asking for `ANSWER:` invites reasoning first, which
  took qwen2.5 from 3 output tokens (0.3 s) to 50-100 (4.8 s). Correct scoring cost ~15x wall time.
- Generalisation for later task families: **the oracle is part of the experiment and needs its own
  test suite.** `lib/tasks.py` extraction now has eight cases covering narration, non-entity
  commits, changed-mind, and answer-first phrasing.
