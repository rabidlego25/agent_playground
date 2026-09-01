"""006 -- where does the ensembling curve saturate on the reasoning prompt?

004 measured C' at k in {1,3,5,7} and the curve was still climbing at its pre-registered
maximum (0.67 -> 0.74 -> 0.83 -> 0.86). It nonetheless concluded that "where the ensembling
curve saturates is a property of the prompt" -- a comparison in which the bare side was
observed and the B1n side was not. This run observes it.

It also puts the repo's main explanatory variable on the line. Conditional-on-wrong agreement
c has carried the argument in 003, 004 and 005 and has only ever been measured, never used to
predict. The pre-registration below states a numeric prediction for k=15 derived from 004's
existing draws, before any new draw is taken.

  samples     eight more B1n draws per task (j=7..14), extending 004's block. 004's seven are
              reused as j=0..6: same model, same prompt, same temperature, same cap, disjoint
              seeds, so all fifteen are exchangeable.
  report      the merged k=1..15 curve, adjacent-k paired tests, and prediction vs outcome.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from _lab import mcnemar, require, wilson             # noqa: E402
from lib.tasks import generate                        # noqa: E402
from lib.trace import Episode, TraceWriter, read      # noqa: E402

N, DEPTH, TEMP = 195, 4, 0.7
MODEL = "ollama:qwen2.5"
SEED0 = 5000
MAX_TOK = 800                    # 004's cap; qwen bound on 0/195 there, so not a factor
SEED_BLOCK = 300                 # continues 004's samples block; 004 used j=0..6 (+300..+306)
K_OLD, K_NEW = 7, 8              # 7 reused from 004 + 8 new = 15
KS = (1, 3, 5, 7, 9, 11, 15)

# Pre-registered before any draw of this experiment (see README).
PREDICTED_K15 = 0.89
PREDICTED_BAND = (0.86, 0.93)
ALTERNATIVE_K15 = 0.862          # plug-in plurality: the curve is already at its asymptote

HERE = Path(__file__).parent
RUNS = HERE / "runs"
ONE = ROOT / "experiments" / "001-deliberation"
FOUR = ROOT / "experiments" / "004-prompt-ceiling" / "runs"


def _prompt_from_001(name: str) -> str:
    """Load B1n out of 001 rather than copying it, as 004 and 005 do."""
    src = ONE / "run.py"
    ns: dict = {"__file__": str(src), "__name__": "_experiment_001"}
    exec(compile(src.read_text(), str(src), "exec"), ns)
    return ns[name]


B1N = _prompt_from_001("B_ONE_N")


def tasks():
    return [generate("multi_hop", SEED0 + s, depth=DEPTH) for s in range(N)]


def _done(stem: str) -> set[str]:
    """task_ids already written, so a killed phase resumes instead of duplicating. 005's
    guard, unchanged -- two runs were killed mid-phase on 2026-09-01."""
    f = RUNS / f"{stem}.jsonl"
    return {e["task_id"] for e in read(f)} if f.exists() else set()


def phase_samples() -> None:
    stem = "006_samples_ext"
    seen = _done(stem)
    b = require(MODEL)
    w = TraceWriter(stem, results_dir=RUNS)
    todo = [t for t in tasks() if t.task_id not in seen]
    for i, t in enumerate(todo):
        ep = Episode(task_id=t.task_id, seed=t.seed,
                     config={"experiment": "006", "phase": "samples", "arm": "C'",
                             "model": MODEL, "k_new": K_NEW, "depth": DEPTH,
                             "temperature": TEMP, "difficulty": t.difficulty,
                             "prompt": "B1n", "max_tokens": MAX_TOK})
        for j in range(K_OLD, K_OLD + K_NEW):
            c = b.complete(B1N.format(original=t.prompt), temperature=TEMP,
                           max_tokens=MAX_TOK, seed=t.seed * 10 + SEED_BLOCK + j)
            parsed, fmt_ok = t.parse(c.text)
            ep.step(state_before=B1N.format(original=t.prompt), action=c.text,
                    tokens_in=c.tokens_in, tokens_out=c.tokens_out,
                    latency_ms=c.latency_ms,
                    meta={"sample": j, "parsed": parsed, "format_ok": fmt_ok,
                          "correct": t.scored(c.text), "error": c.error,
                          "cap_bound": c.tokens_out >= MAX_TOK})
        ep.finish(verdict=ep.steps[0].meta["correct"], outcome=ep.steps[0].meta["parsed"])
        w.write(ep)
        print(f"\r  samples {len(seen) + i + 1}/{N}", end="", flush=True)
    print()


def vote(sel: list[str]) -> str:
    """Plurality, ties toward the earliest draw. 004's _vote and lib majority(), unchanged."""
    c = Counter(sel)
    top = max(c.values())
    return next(a for a in sel if c[a] == top)


def _draws() -> tuple[dict[str, list[str]], dict[str, list[tuple[int, int]]]]:
    """Fifteen answers per task: 004's seven then this run's eight, in seed order."""
    old = {e["task_id"]: e for e in read(FOUR / "004_samples.jsonl")}
    new = {e["task_id"]: e for e in read(RUNS / "006_samples_ext.jsonl")}
    missing = set(old) - set(new)
    if missing:
        sys.exit(f"{len(missing)} tasks have no extension draws; run the samples phase first")
    d, tok = {}, {}
    for i in old:
        steps = old[i]["steps"] + new[i]["steps"]
        d[i] = [s["meta"]["parsed"].lower() for s in steps]
        tok[i] = [(s["tokens_in"], s["tokens_out"]) for s in steps]
    return d, tok


def report() -> None:
    ts = tasks()
    gold = {t.task_id: t.answer.lower() for t in ts}
    ids = [t.task_id for t in ts]
    d, tok = _draws()

    print(f"006 -- ensembling asymptote, multi_hop d={DEPTH}, temp={TEMP}, "
          f"{MODEL.split(':', 1)[1]}, B1n, n={N}")
    print(f"pre-registered: k=15 = {PREDICTED_K15:.2f} "
          f"[{PREDICTED_BAND[0]:.2f},{PREDICTED_BAND[1]:.2f}]; "
          f"named alternative (plug-in): {ALTERNATIVE_K15:.3f}\n")

    hits = {}
    print(f"{'k':>3} {'acc':>6}  {'95% CI':<14} {'tok_in':>9} {'tok_out':>9} {'total':>10}")
    for k in KS:
        h = [vote(d[i][:k]) == gold[i] for i in ids]
        hits[k] = h
        a = sum(h) / N
        lo, hi = wilson(sum(h), N)
        ti = sum(t[0] for i in ids for t in tok[i][:k])
        to = sum(t[1] for i in ids for t in tok[i][:k])
        print(f"{k:>3} {a:>6.3f}  [{lo:.2f},{hi:.2f}]   {ti:>9,} {to:>9,} {ti + to:>10,}")

    print("\nadjacent-k, paired exact McNemar:")
    for a, b in zip(KS, KS[1:]):
        f, s, p = mcnemar(hits[a], hits[b])
        star = "  **" if p < 0.05 else ""
        print(f"  k={a:<2} -> k={b:<2}  {sum(hits[a])/N:.3f} -> {sum(hits[b])/N:.3f}  "
              f"{f:>3} {s:>3}  p={p:.4f}{star}")

    k15 = sum(hits[15]) / N
    lo, hi = PREDICTED_BAND
    verdict = ("PREDICTION HELD" if lo <= k15 <= hi else
               "PREDICTION FAILED -- plug-in was right, curve had saturated"
               if k15 < lo else "PREDICTION FAILED -- both estimators underestimated")
    print(f"\nk=15 measured {k15:.3f} vs predicted {PREDICTED_K15:.2f} "
          f"[{lo:.2f},{hi:.2f}]: {verdict}")

    ceil = sum(any(a == gold[i] for a in d[i]) for i in ids) / N
    print(f"\nheadroom: correct answer appears in at least one of 15 draws on {ceil:.3f} "
          f"of tasks.\n  voting cannot exceed this; the gap to k=15 is what plurality "
          f"loses that sampling found.")

    nb = sum(1 for e in read(RUNS / "006_samples_ext.jsonl")
             for s in e["steps"] if s["meta"].get("cap_bound"))
    print(f"\ncap binding in the new draws: {nb}/{N * K_NEW} "
          f"({nb / (N * K_NEW):.1%})   [004: 0/1365]")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    {"samples": phase_samples, "report": report}[cmd]()
