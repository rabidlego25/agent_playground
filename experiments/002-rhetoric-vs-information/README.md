# 002 — Does rhetorical packaging change what a reader agent does?

**Status:** designed, not run. **Created:** 2026-08-29.

## Motivation

`CLAUDE.md` now carries a writing-style convention. It was written from taste, which is a bad reason
for a project rule. The underlying claim is empirical and this repo can test it.

The claim has teeth because of how experiment 001 could fail. If agents in a deliberation arm move each
other by *confidence* rather than by *information*, then k communicating agents can converge on a wrong
answer faster than one agent alone would. That makes rhetoric a mechanism by which deliberation actively
hurts — and it would be invisible in an accuracy-only score, because a confident wrong consensus and a
confident right consensus look identical from outside.

## Definition being used

**Fluff = text that can be deleted without changing what a downstream reader does.** This is
operational, not aesthetic: it makes information density measurable as Δ(downstream accuracy) per token.

## Hypotheses

- **H1 (compressibility).** Downstream accuracy is flat as a note is compressed from 1.0L to ~0.3L, then
  falls. The plateau width estimates the fluff fraction.
- **H2 (confidence attack).** For a note containing one planted false claim, higher rhetorical confidence
  in the packaging **lowers** the reader's rate of catching it, at equal information content.
  *This is the one that matters.* H1 is about efficiency; H2 is about whether polish is harmful.
- **H3 (rejected-alternatives).** Notes that record rejected options outperform conclusion-only notes of
  equal length when the reader faces a decision adjacent to the original one — because the reader does not
  re-derive. Carried over from `notes/2026-08-29-benchmark-vs-instrument.md`.

## Design

Reuse the existing rig: `lib/tasks.py` for ground truth, `lib/trace.py` for episodes, `tests/_lab.py`
for Wilson intervals and cell tables.

1. **Writer A** solves a `multi_hop` or `assignment_puzzle` instance and writes a handoff note.
2. **Style transform** rewrites that note into arms while holding claim content fixed:
   - `plain` — claims only, no emphasis, no summary line.
   - `polished` — bolded lead-ins, an aphoristic closer, assertive framing.
   - `compressed-{50,25,10}%` — length-targeted rewrites (H1).
   - `hedged` — same claims, explicit uncertainty markers.
3. **Reader B** (fresh context, no access to the original task) answers a question answerable only from
   the note. Score with the existing `ANSWER:` oracle.
4. **H2 arm:** inject exactly one false claim. Score whether B flags it. Reader is told a note *may*
   contain an error, so flagging is licensed and a non-flag is a real miss.

**Controls that make it interpretable**
- Style transform must not change claim content. Verify by extracting claim sets from both versions and
  diffing; discard any pair that differs. Without this, the experiment measures paraphrase, not style.
- Token-match arms, or report accuracy per token. `polished` is longer by construction.
- Writer and reader should be the *same* model in the primary arm, so the result is about text rather
  than about a capability gap; vary it in a secondary arm.
- Read every effect against the noise floor from `tests/probe_variance_floor.py`.

## Interpretation

- H2 holds → the style rule in `CLAUDE.md` is a safety property, not taste, and 001 needs a
  consensus-confidence measure alongside accuracy.
- H2 fails, H1 holds → the rule is only about efficiency. Keep it, downgrade the justification.
- H3 holds → it generalises past this repo: it is a claim about what agent memory and context
  compaction should preserve, and compaction that keeps conclusions while dropping the search is
  lossy in a biased direction.

## Known weaknesses

- "Rhetorical confidence" is operationalised by a rewrite prompt, so the transform's own biases are
  inside the treatment. Manual inspection of a sample is required before trusting any result.
- A planted-error task may be easier than real error detection, where nobody says an error exists.
- Small local models may not track rhetorical register at all, giving a null that is about the reader's
  capability rather than about style. Run at ≥2 capability points before concluding anything.
