"""004 -- does the ensembling gain survive at the top of the prompt axis?

001 measured its whole configuration curve on a prompt that does not ask the model to
reason, then found that one sentence of prompt (arm B1n) beats every arm in it at a tenth
the cost. This re-runs 001's `samples` phase changing exactly one thing: the prompt.

  samples     k_max independent draws per task under the B1n prompt. Arm A' is the k=1
              prefix, C' at any k <= k_max is the k-prefix of the same draws.
  deliberate  arm D'. Same revision protocol as 001, on the reasoning prompt.
  report      the C' curve, paired against 001's bare-prompt arms on identical instances,
              plus the error-correlation statistic H3 is stated in terms of.

Everything except the prompt is byte-identical to 001: same n, depth, temperature, model,
seeds, k_max. The prompt itself is not retyped -- it is loaded out of 001's run.py so the
two arms cannot drift apart silently.
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

N, DEPTH, TEMP, K_MAX, K_DELIB = 195, 4, 0.7, 7, 3
MODEL = "ollama:qwen2.5"
SEED0 = 5000                     # identical block to 001 and 003, so all arms pair
MAX_TOK = 800                    # B1n's cap in 001; not binding either way (mean out ~104)
SEED_BLOCK = 300                 # disjoint from 001 samples(+j) / delib(+100) / budget(+200)

ONE = ROOT / "experiments" / "001-deliberation"


def _prompt_from_001(name: str) -> str:
    """Load a prompt template out of 001 rather than copying it here. A copy would be a
    silent confound the first time either file is edited; this is a hard link."""
    src = ONE / "run.py"
    ns: dict = {"__file__": str(src), "__name__": "_experiment_001"}
    exec(compile(src.read_text(), str(src), "exec"), ns)
    return ns[name]


B1N = _prompt_from_001("B_ONE_N")
PEER_TEMPLATE = _prompt_from_001("PEER_TEMPLATE")
RUNS = Path(__file__).parent / "runs"


def tasks():
    return [generate("multi_hop", SEED0 + s, depth=DEPTH) for s in range(N)]


def phase_samples() -> None:
    b = require(MODEL)
    w = TraceWriter("004_samples", results_dir=RUNS)
    for i, t in enumerate(tasks()):
        ep = Episode(task_id=t.task_id, seed=t.seed,
                     config={"experiment": "004", "phase": "samples", "arm": "A'/C'",
                             "model": MODEL, "k_max": K_MAX, "depth": DEPTH,
                             "temperature": TEMP, "difficulty": t.difficulty,
                             "prompt": "B1n", "max_tokens": MAX_TOK})
        for j in range(K_MAX):
            c = b.complete(B1N.format(original=t.prompt), temperature=TEMP,
                           max_tokens=MAX_TOK, seed=t.seed * 10 + SEED_BLOCK + j)
            parsed, fmt_ok = t.parse(c.text)
            ep.step(state_before=B1N.format(original=t.prompt), action=c.text,
                    tokens_in=c.tokens_in, tokens_out=c.tokens_out,
                    latency_ms=c.latency_ms,
                    meta={"sample": j, "parsed": parsed, "format_ok": fmt_ok,
                          "correct": t.scored(c.text), "error": c.error})
        ep.finish(verdict=ep.steps[0].meta["correct"], outcome=ep.steps[0].meta["parsed"])
        w.write(ep)
        print(f"\r  samples {i + 1}/{N}", end="", flush=True)
    print()


def phase_deliberate() -> None:
    """Arm D'. Same protocol as 001's arm D -- reuse the first K_DELIB draws as round one,
    show each agent the other two in full, take one revision round, vote over the revised
    answers. The revision template is 001's, unmodified."""
    b = require(MODEL)
    src = {e["task_id"]: e for e in read(RUNS / "004_samples.jsonl")}
    w = TraceWriter("004_deliberate", results_dir=RUNS)
    for i, t in enumerate(tasks()):
        prior = src.get(t.task_id)
        if prior is None:
            sys.exit(f"no round-one samples for {t.task_id}; run the samples phase first")
        round1 = prior["steps"][:K_DELIB]
        ep = Episode(task_id=t.task_id, seed=t.seed,
                     config={"experiment": "004", "phase": "deliberate", "arm": "D'",
                             "model": MODEL, "k": K_DELIB, "depth": DEPTH,
                             "temperature": TEMP, "difficulty": t.difficulty,
                             "prompt": "B1n", "round1_run_id": prior["run_id"]})
        for j in range(K_DELIB):
            peers = "\n\n".join(
                f"Assistant {chr(65 + m)} said:\n{round1[m]['action']}"
                for m in range(K_DELIB) if m != j)
            prompt = PEER_TEMPLATE.format(original=t.prompt, peers=peers)
            c = b.complete(prompt, temperature=TEMP, max_tokens=MAX_TOK,
                           seed=t.seed * 10 + SEED_BLOCK + 100 + j)
            parsed, fmt_ok = t.parse(c.text)
            ep.step(state_before=prompt, action=c.text, tokens_in=c.tokens_in,
                    tokens_out=c.tokens_out, latency_ms=c.latency_ms,
                    meta={"agent": j, "parsed": parsed, "format_ok": fmt_ok,
                          "correct": t.scored(c.text), "error": c.error,
                          "round1_parsed": round1[j]["meta"]["parsed"],
                          "changed_mind": parsed.lower() != round1[j]["meta"]["parsed"].lower()})
        votes = Counter(s.meta["parsed"].lower() for s in ep.steps)
        won = votes.most_common(1)[0][0]
        ep.finish(verdict=won == str(t.answer).lower(), outcome=won)
        w.write(ep)
        print(f"\r  deliberate {i + 1}/{N}", end="", flush=True)
    print()


# ---------------------------------------------------------------- analysis


def _vote(steps: list[dict], k: int) -> str:
    """Majority over the first k draws, ties broken toward the earliest sample. Matches
    lib majority() and 001's report(), so the two curves are computed the same way."""
    sel = steps[:k]
    votes = Counter(s["meta"]["parsed"].lower() for s in sel)
    top = max(votes.values())
    return next(s["meta"]["parsed"].lower() for s in sel
                if votes[s["meta"]["parsed"].lower()] == top)


def _curve(eps: list[dict], gold: dict[str, str]) -> dict[int, dict]:
    out = {}
    for k in (1, 3, 5, 7):
        hits = [(_vote(e["steps"], k) == gold[e["task_id"]]) for e in eps]
        ti = sum(s["tokens_in"] for e in eps for s in e["steps"][:k])
        to = sum(s["tokens_out"] for e in eps for s in e["steps"][:k])
        out[k] = {"hits": hits, "acc": sum(hits) / len(hits), "ti": ti, "to": to}
    return out


def _cond_wrong_agreement(eps: list[dict], gold: dict[str, str]) -> tuple[float, int]:
    """P(draw j gives the same answer as draw i | draw i is wrong), over ordered pairs.

    This is the error independence that majority voting spends. It is comparable across
    prompts without a null model: it conditions on being wrong, so a change in base rate
    does not move it by itself.
    """
    same = tot = 0
    for e in eps:
        ans = [s["meta"]["parsed"].lower() for s in e["steps"]]
        g = gold[e["task_id"]]
        for i, ai in enumerate(ans):
            if ai == g:
                continue
            for j, aj in enumerate(ans):
                if i == j:
                    continue
                tot += 1
                same += aj == ai
    return (same / tot if tot else 0.0), tot


def _consensus(eps: list[dict], gold: dict[str, str], k: int = 3) -> dict[int, tuple[int, float]]:
    rows: dict[int, list[bool]] = {}
    for e in eps:
        sel = e["steps"][:k]
        d = len({s["meta"]["parsed"].lower() for s in sel})
        rows.setdefault(d, []).append(_vote(e["steps"], k) == gold[e["task_id"]])
    return {d: (len(v), sum(v) / len(v)) for d, v in sorted(rows.items())}


def _row(label: str, acc: float, n: int, ti: int, to: int) -> str:
    lo, hi = wilson(round(acc * n), n)
    return f"{label:<30} {acc:>6.2f}  [{lo:.2f},{hi:.2f}]  {ti:>8} {to:>8} {ti + to:>8}"


def report() -> None:
    ts = tasks()
    gold = {t.task_id: str(t.answer).lower() for t in ts}
    new = read(RUNS / "004_samples.jsonl")
    old = read(ONE / "runs" / "001_samples.jsonl")
    by = lambda eps: {e["task_id"]: e for e in eps}                       # noqa: E731
    new, old = by(new), by(old)
    ids = [t.task_id for t in ts if t.task_id in new and t.task_id in old]
    new = [new[i] for i in ids]
    old = [old[i] for i in ids]
    n = len(ids)
    print(f"\n004 -- multi_hop d={DEPTH}, temp={TEMP}, {MODEL}, n={n} (paired with 001)\n")

    C_new, C_old = _curve(new, gold), _curve(old, gold)
    print(f"{'arm':<30} {'acc':>6}  {'95% CI':<13} {'tok_in':>8} {'tok_out':>8} {'total':>8}")
    for k in (1, 3, 5, 7):
        lab = "A: single sample" if k == 1 else f"C: k={k} vote"
        print(_row(f"{lab}, bare", C_old[k]["acc"], n, C_old[k]["ti"], C_old[k]["to"]))
    print()
    for k in (1, 3, 5, 7):
        lab = "A': single sample" if k == 1 else f"C': k={k} vote"
        print(_row(f"{lab}, B1n", C_new[k]["acc"], n, C_new[k]["ti"], C_new[k]["to"]))

    dpath = RUNS / "004_deliberate.jsonl"
    if dpath.exists():
        D = by(read(dpath))
        D = [D[i] for i in ids if i in D]
        if len(D) == n:
            hits = [bool(e["verdict"]) for e in D]
            ti = C_new[K_DELIB]["ti"] + sum(e["tokens_in_total"] for e in D)
            to = C_new[K_DELIB]["to"] + sum(e["tokens_out_total"] for e in D)
            print(_row(f"D': k={K_DELIB} + 1 revision", sum(hits) / n, n, ti, to))
            C_new["D"] = {"hits": hits, "acc": sum(hits) / n}

    print("\npaired exact McNemar (all arms on identical instances):")
    print(f"{'contrast':<34} {'acc':>13}  {'1st':>4} {'2nd':>4}  {'p':>7}")

    def show(lab, a, b):
        x, y, p = mcnemar(a, b)
        print(f"{lab:<34} {sum(a)/n:>5.2f} -> {sum(b)/n:<5.2f}  {x:>4} {y:>4}  {p:>7.4f}")

    for k in (3, 5, 7):
        show(f"A' vs C'{k}  (H1, B1n prompt)", C_new[1]["hits"], C_new[k]["hits"])
    print()
    for k in (1, 3, 5, 7):
        lab = "A" if k == 1 else f"C{k}"
        show(f"{lab} bare vs {lab}' B1n", C_old[k]["hits"], C_new[k]["hits"])
    if "D" in C_new:
        print()
        for k in (3, 5, 7):
            show(f"C'{k} vs D'", C_new[k]["hits"], C_new["D"]["hits"])

    print("\nH2 -- ensembling gain, bare vs B1n (difference of differences):")
    print(f"{'k':<4} {'gain bare':>10} {'gain B1n':>10} {'delta':>8}")
    for k in (3, 5, 7):
        gb = C_old[k]["acc"] - C_old[1]["acc"]
        gn = C_new[k]["acc"] - C_new[1]["acc"]
        print(f"{k:<4} {gb:>+10.3f} {gn:>+10.3f} {gn - gb:>+8.3f}")
    print("  run-to-run variance floor 0.050 (reports/2026-08-30-calibration.pdf)")

    print("\nH3 -- error correlation: P(second draw repeats the first's answer | first is wrong)")
    for lab, eps in (("bare prompt", old), ("B1n prompt", new)):
        c, tot = _cond_wrong_agreement(eps, gold)
        print(f"  {lab:<12} c={c:.3f}  over {tot} ordered pairs")

    print("\nconsensus at k=3 (distinct answers -> tasks, majority correct):")
    print(f"{'distinct':<10} {'bare: n':>8} {'bare: acc':>10} {'B1n: n':>8} {'B1n: acc':>10}")
    cb, cn = _consensus(old, gold), _consensus(new, gold)
    for d in sorted(set(cb) | set(cn)):
        bn, ba = cb.get(d, (0, float('nan')))
        nn, na = cn.get(d, (0, float('nan')))
        print(f"{d:<10} {bn:>8} {ba:>10.2f} {nn:>8} {na:>10.2f}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    {"samples": phase_samples, "deliberate": phase_deliberate, "report": report}[cmd]()
