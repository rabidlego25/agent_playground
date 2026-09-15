# ASSESS — schema

Every experiment carries an `ASSESS.md` alongside its `README.md`.

**They have different readers.** The README is the lab notebook: narrative, ordered by how the
work actually went, addressed to someone with the repo open. `ASSESS.md` is addressed to a
model with **no access to this repo's history**, asked one question: *is the headline claim
supported by what was actually measured?* It must be self-contained enough to answer that, and
must point at artifacts precise enough that the assessor can recompute rather than believe.

Fixed sections, in this order. Target 60–90 lines. If a section is empty, write why.

```
## 1. Claim          One sentence. The thing to be judged. Not a summary of the experiment.
## 2. Status         Date, complete/partial/unrun, model calls spent, money spent.
## 3. Pre-registered Hypotheses as written BEFORE the run, with the commit that fixed them.
                     Mark anything added or amended later as post hoc, explicitly.
## 4. Method         Models (exact ids), prompt condition, task family, n, what varied, what
                     was held fixed, the statistical test and why that one.
## 5. Result         Numbers with intervals. Which hypotheses survived, which did not.
## 6. Threats        What could make the claim wrong. What was ruled out, and by what check.
                     Anything still open stays open here -- this section is not a defence.
## 7. Artifacts      Files an assessor recomputes from: traces, run scripts, probes. Paths.
## 8. Challenge      The 3-5 questions this experiment most wants attacked, written by whoever
                     ran it. Name the weakest link yourself.
```

## Why section 8 exists

Without it an assessing model produces generic methodology commentary -- "consider a larger
sample", "report confidence intervals" -- which is free to write and worth nothing. Naming the
specific weak link converts the assessment into a check on a real claim.

The honesty constraint is the same one in `notes/2026-08-29-oracle-format-confound.md`: an
`ASSESS.md` that reads as a defence brief is worse than none, because it spends the assessor's
attention on the parts that are already sound. Section 6 and section 8 are the load-bearing
ones; 1-5 exist so the assessor can check them.

## Rule

`ASSESS.md` states no number that is not either in the README or recomputable from §7. An
assessable write-up that is itself unverified is the failure this repo keeps finding.
