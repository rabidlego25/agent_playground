"""005 -- does the mixed panel clear the Condorcet threshold at the prompt ceiling?

003 ran a mixed-family panel on the bare prompt and could not test its own question: two
of three members sat far below the competence a majority vote needs (qwen 0.51, llama
0.22, mistral 0.18), so the vote landed below its best member. 004 then showed that prompt
is worth +0.16 to qwen and, more importantly, that a reasoning prompt *raises* error
independence instead of spending it.

This is 003 with one thing changed: the prompt. Same panel, tasks, seeds, voting rule and
revision wording.

  samples <model>     one B1n draw per task from one panel member. llama3.1 and mistral
                      only -- qwen2.5's draw is reused from 004 at the same seed from the
                      same weights, exactly as 003 reused 001's.
  deliberate <model>  that member's revision after seeing the other two.
  report              per-member prompt effect (H2), the panel arms, cross-family error
                      independence (H3) and the capability-transfer table (H4).

Phases are per-model rather than per-task for the reason 003 gives: a 16 GB machine holds
two 7-8B models and not three, so interleaving per task would thrash on model load.
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
MAX_TOK = 800                    # identical to 004; per-model caps would confound cap with model
SEED0 = 5000
SEED_SAMPLES = 300               # matches 004's samples block
SEED_DELIB = 500                 # disjoint from 004's revision block (+400+j)
PANEL = ["ollama:qwen2.5", "ollama:llama3.1", "ollama:mistral:7b"]

HERE = Path(__file__).parent
RUNS = HERE / "runs"
ONE = ROOT / "experiments" / "001-deliberation"
THREE = ROOT / "experiments" / "003-mixed-panel" / "runs"
FOUR = ROOT / "experiments" / "004-prompt-ceiling" / "runs"

slug = lambda m: m.split(":", 1)[1].replace(":", "-")           # noqa: E731


def _prompt_from_001(name: str) -> str:
    """Load prompt templates out of 001 rather than copying them, so 001/004/005 cannot
    drift apart silently. Same mechanism 004 uses."""
    src = ONE / "run.py"
    ns: dict = {"__file__": str(src), "__name__": "_experiment_001"}
    exec(compile(src.read_text(), str(src), "exec"), ns)
    return ns[name]


B1N = _prompt_from_001("B_ONE_N")
PEER_TEMPLATE = _prompt_from_001("PEER_TEMPLATE")


def tasks():
    return [generate("multi_hop", SEED0 + s, depth=DEPTH) for s in range(N)]


def round_one(model: str) -> dict:
    """This member's round-one B1n answers, keyed by task_id."""
    if model == PANEL[0]:                   # reuse 004's j=0 draw: same weights, same seed
        return {e["task_id"]: e["steps"][0] for e in read(FOUR / "004_samples.jsonl")}
    return {e["task_id"]: e["steps"][0]
            for e in read(RUNS / f"005_samples_{slug(model)}.jsonl")}


def phase_samples(model: str) -> None:
    if model == PANEL[0]:
        sys.exit("qwen2.5's B1n draw is reused from 004; do not redraw it")
    b = require(model)
    w = TraceWriter(f"005_samples_{slug(model)}", results_dir=RUNS)
    for i, t in enumerate(tasks()):
        prompt = B1N.format(original=t.prompt)
        c = b.complete(prompt, temperature=TEMP, max_tokens=MAX_TOK,
                       seed=t.seed * 10 + SEED_SAMPLES)
        parsed, fmt_ok = t.parse(c.text)
        ep = Episode(task_id=t.task_id, seed=t.seed,
                     config={"experiment": "005", "phase": "samples", "model": model,
                             "depth": DEPTH, "temperature": TEMP, "prompt": "B1n",
                             "max_tokens": MAX_TOK, "difficulty": t.difficulty})
        ep.step(state_before=prompt, action=c.text, tokens_in=c.tokens_in,
                tokens_out=c.tokens_out, latency_ms=c.latency_ms,
                meta={"parsed": parsed, "format_ok": fmt_ok,
                      "correct": t.scored(c.text), "error": c.error,
                      # a completion that hits the cap loses its ANSWER: line and scores
                      # wrong, which is an instrument artifact, not a capability result
                      "cap_bound": c.tokens_out >= MAX_TOK})
        ep.finish(verdict=t.scored(c.text), outcome=parsed)
        w.write(ep)
        print(f"\r  samples {slug(model)} {i + 1}/{N}", end="", flush=True)
    print()


def phase_deliberate(model: str) -> None:
    b = require(model)
    j = PANEL.index(model)
    r1 = [round_one(m) for m in PANEL]
    w = TraceWriter(f"005_delib_{slug(model)}", results_dir=RUNS)
    for i, t in enumerate(tasks()):
        peers = "\n\n".join(f"Assistant {chr(65 + m)} said:\n{r1[m][t.task_id]['action']}"
                            for m in range(len(PANEL)) if m != j)
        prompt = PEER_TEMPLATE.format(original=t.prompt, peers=peers)
        c = b.complete(prompt, temperature=TEMP, max_tokens=MAX_TOK,
                       seed=t.seed * 10 + SEED_DELIB + j)
        parsed, fmt_ok = t.parse(c.text)
        prior = r1[j][t.task_id]["meta"]["parsed"]
        ep = Episode(task_id=t.task_id, seed=t.seed,
                     config={"experiment": "005", "phase": "deliberate", "model": model,
                             "agent": j, "depth": DEPTH, "temperature": TEMP,
                             "prompt": "B1n", "difficulty": t.difficulty})
        ep.step(state_before=prompt, action=c.text, tokens_in=c.tokens_in,
                tokens_out=c.tokens_out, latency_ms=c.latency_ms,
                meta={"agent": j, "parsed": parsed, "format_ok": fmt_ok,
                      "correct": t.scored(c.text), "error": c.error,
                      "round1_parsed": prior, "cap_bound": c.tokens_out >= MAX_TOK,
                      "changed_mind": parsed.lower() != prior.lower()})
        ep.finish(verdict=t.scored(c.text), outcome=parsed)
        w.write(ep)
        print(f"\r  deliberate {slug(model)} {i + 1}/{N}", end="", flush=True)
    print()


def vote(answers: list[str]) -> str:
    """Majority, tie-broken toward the earliest panel member -- 001's and 003's rule."""
    c = Counter(answers)
    top = max(c.values())
    return next(a for a in answers if c[a] == top)


def _cross_family_c(tab: dict, ids: list[str], gold: dict) -> tuple[float, int]:
    """P(another family's answer repeats this one | this one is wrong), over ordered pairs.
    The cross-family analogue of 004's within-family statistic."""
    same = tot = 0
    for i in ids:
        a = [tab[m][i]["meta"]["parsed"].lower() for m in PANEL]
        for x, ax in enumerate(a):
            if ax == gold[i]:
                continue
            for y, ay in enumerate(a):
                if x != y:
                    tot += 1
                    same += ay == ax
    return (same / tot if tot else 0.0), tot


def _bare_tables(ids: list[str]) -> dict:
    """003's bare-prompt draws, for the paired per-member prompt effect (H2)."""
    out = {PANEL[0]: {e["task_id"]: e["steps"][0]
                      for e in read(ONE / "runs" / "001_samples.jsonl")}}
    for m in PANEL[1:]:
        out[m] = {e["task_id"]: e["steps"][0]
                  for e in read(THREE / f"003_samples_{slug(m)}.jsonl")}
    return out


def report() -> None:
    ts = tasks()
    gold = {t.task_id: str(t.answer).lower() for t in ts}
    pre = {m: round_one(m) for m in PANEL}
    ids = [t.task_id for t in ts if all(t.task_id in pre[m] for m in PANEL)]
    bare = _bare_tables(ids)
    post = {}
    for m in PANEL:
        p = RUNS / f"005_delib_{slug(m)}.jsonl"
        if p.exists():
            post[m] = {e["task_id"]: e["steps"][0] for e in read(p)}

    n = len(ids)
    print(f"\n005 -- mixed panel at the prompt ceiling, multi_hop d={DEPTH}, "
          f"temp={TEMP}, n={n}")
    print("     " + " / ".join(slug(m) for m in PANEL) + "\n")
    print(f"{'arm':<34} {'acc':>6}  {'95% CI':<13} {'tok_in':>8} {'tok_out':>8} {'total':>8}")

    def line(label, hits, ti, to):
        lo, hi = wilson(hits, n)
        print(f"{label:<34} {hits / n:>6.2f}  [{lo:.2f},{hi:.2f}]"
              f"  {ti:>8} {to:>8} {ti + to:>8}")

    hit = lambda tab, m, i: tab[m][i]["meta"]["parsed"].lower() == gold[i]   # noqa: E731
    for m in PANEL:
        line(f"  solo bare:  {slug(m)}", sum(hit(bare, m, i) for i in ids),
             sum(bare[m][i]["tokens_in"] for i in ids),
             sum(bare[m][i]["tokens_out"] for i in ids))
    print()
    for m in PANEL:
        line(f"  solo B1n:   {slug(m)}", sum(hit(pre, m, i) for i in ids),
             sum(pre[m][i]["tokens_in"] for i in ids),
             sum(pre[m][i]["tokens_out"] for i in ids))

    print()
    ti = sum(pre[m][i]["tokens_in"] for m in PANEL for i in ids)
    to = sum(pre[m][i]["tokens_out"] for m in PANEL for i in ids)
    cvotes = [vote([pre[m][i]["meta"]["parsed"].lower() for m in PANEL]) == gold[i]
              for i in ids]
    line("C-mixed': k=3 vote, no comms", sum(cvotes), ti, to)
    if len(post) == len(PANEL):
        dvotes = [vote([post[m][i]["meta"]["parsed"].lower() for m in PANEL]) == gold[i]
                  for i in ids]
        line("D-mixed': k=3 + revision round", sum(dvotes),
             ti + sum(post[m][i]["tokens_in"] for m in PANEL for i in ids),
             to + sum(post[m][i]["tokens_out"] for m in PANEL for i in ids))

    print("\nH2 -- per-member prompt effect, paired exact McNemar (bare -> B1n):")
    print(f"{'member':<16} {'bare':>6} {'B1n':>6} {'delta':>7}  {'1st':>4} {'2nd':>4}  {'p':>7}")
    for m in PANEL:
        a = [hit(bare, m, i) for i in ids]
        b = [hit(pre, m, i) for i in ids]
        x, y, p = mcnemar(a, b)
        print(f"{slug(m):<16} {sum(a)/n:>6.2f} {sum(b)/n:>6.2f} {sum(b)/n - sum(a)/n:>+7.3f}"
              f"  {x:>4} {y:>4}  {p:>7.4f}")

    best = max(PANEL, key=lambda m: sum(hit(pre, m, i) for i in ids))
    ba = [hit(pre, best, i) for i in ids]
    x, y, p = mcnemar(ba, cvotes)
    print(f"\nH1 (gate) -- best member ({slug(best)}) vs C-mixed': "
          f"{sum(ba)/n:.2f} -> {sum(cvotes)/n:.2f}  {x} {y}  p={p:.4f}"
          f"   [003, bare: 0.51 -> 0.43, p=0.0070]")

    print("\nH3 -- cross-family error independence")
    for lab, tab, ref in (("bare  (003)", bare, ""), ("B1n   (005)", pre, "")):
        c, tot = _cross_family_c(tab, ids, gold)
        print(f"  {lab}  c={c:.3f}  over {tot} ordered pairs{ref}")
    print("  reference: within-family bare 0.339 (001), within-family B1n 0.239 (004)")

    print("\ncap binding (a truncated completion loses its ANSWER: line):")
    for m in PANEL:
        cb = sum(bool(pre[m][i]["meta"].get("cap_bound")) for i in ids)
        print(f"  {slug(m):<16} {cb:>3}/{n} ({cb / n:.1%})"
              + ("   ** >5%: solo rate is a LOWER BOUND, re-run at 1600 **"
                 if cb / n > 0.05 else ""))

    if len(post) == len(PANEL):
        print("\nH4 -- capability transfer, per member (pre -> post deliberation):")
        print(f"{'member':<16} {'pre':>6} {'post':>6} {'delta':>7} {'changed':>8} "
              f"{'w->r':>5} {'r->w':>5} {'net':>5}")
        for m in PANEL:
            pr = [hit(pre, m, i) for i in ids]
            po = [hit(post, m, i) for i in ids]
            ch = sum(post[m][i]["meta"]["changed_mind"] for i in ids)
            wr = sum(1 for i in ids if not hit(pre, m, i) and hit(post, m, i))
            rw = sum(1 for i in ids if hit(pre, m, i) and not hit(post, m, i))
            print(f"{slug(m):<16} {sum(pr)/n:>6.2f} {sum(po)/n:>6.2f} "
                  f"{sum(po)/n - sum(pr)/n:>+7.3f} {ch/n:>7.0%} {wr:>5} {rw:>5} {wr - rw:>+5}")
        print("  [003, bare: mistral +0.13 (56% adopted a peer), llama -0.03 (35%), qwen -0.01]")

        for label, tab in (("pre", pre), ("post", post)):
            rows: dict[int, list[bool]] = {}
            for i in ids:
                ans = [tab[m][i]["meta"]["parsed"].lower() for m in PANEL]
                rows.setdefault(len(set(ans)), []).append(vote(ans) == gold[i])
            print(f"  {label}-deliberation agreement:")
            for d in sorted(rows):
                v = rows[d]
                print(f"    {d} distinct: {len(v):3d} tasks, majority correct {sum(v)/len(v):.2f}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    if cmd == "report":
        report()
    else:
        arg = sys.argv[2]
        match = [m for m in PANEL if arg in (m, slug(m), m.split(":", 1)[1])]
        if len(match) != 1:
            sys.exit(f"{arg!r} matches {len(match)} panel members; use one of: "
                     + ", ".join(slug(m) for m in PANEL))
        {"samples": phase_samples, "deliberate": phase_deliberate}[cmd](match[0])
