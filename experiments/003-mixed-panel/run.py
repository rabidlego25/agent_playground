"""003 -- does a mixed-family panel restore what deliberation destroys?

001 found that deliberation costs 1.85x a non-communicating control for identical
accuracy, and proposed a mechanism: agents move together, so discussion spends the error
independence that majority voting depends on. That explanation predicts its own escape
hatch. Three instances of one model share weights and converge easily; three *different
families* do not have that shortcut, so if correlation is the problem, varying family
should shrink it.

If D still fails here, the correlation explanation in 001 is wrong and the null is about
deliberation itself rather than about who is deliberating.

Panel is size-matched (7-8B) so family varies and capacity does not. Tasks, seeds and
depth are identical to 001, so every arm here is paired against every arm there.

  samples <model>     one sample per task from one panel member. Run once per member.
                      qwen2.5 is not re-run: 001's samples phase already drew it at the
                      same seed from the same weights, so it is reused verbatim.
  deliberate <model>  that member's revision after seeing the other two.
  report              assembles the panel and compares against 001.

Phases are per-model rather than per-task on purpose: a 16 GB machine holding two 7-8B
models is fine, three is not, so interleaving families per task would thrash on model
load. One pass per model is one load per model.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))

from _lab import require, wilson                      # noqa: E402
from lib.tasks import generate                        # noqa: E402
from lib.trace import Episode, TraceWriter, read      # noqa: E402

N, DEPTH, TEMP, MAX_TOK = 195, 4, 0.7, 400
SEED0 = 5000                     # identical task instances to 001
PANEL = ["ollama:qwen2.5", "ollama:llama3.1", "ollama:mistral:7b"]
RUNS = Path(__file__).parent / "runs"
ONE = Path(__file__).resolve().parents[1] / "001-deliberation" / "runs"

slug = lambda m: m.split(":", 1)[1].replace(":", "-")


def tasks():
    return [generate("multi_hop", SEED0 + s, depth=DEPTH) for s in range(N)]


def round_one(model: str) -> dict:
    """This member's round-one answers, keyed by task_id."""
    if model == PANEL[0]:                       # reuse 001's j=0 draw, same seed
        return {e["task_id"]: e["steps"][0] for e in read(ONE / "001_samples.jsonl")}
    return {e["task_id"]: e["steps"][0] for e in read(RUNS / f"003_samples_{slug(model)}.jsonl")}


def phase_samples(model: str) -> None:
    b = require(model)
    w = TraceWriter(f"003_samples_{slug(model)}", results_dir=RUNS)
    for i, t in enumerate(tasks()):
        c = b.complete(t.prompt, temperature=TEMP, max_tokens=MAX_TOK, seed=t.seed * 10)
        parsed, fmt_ok = t.parse(c.text)
        ep = Episode(task_id=t.task_id, seed=t.seed,
                     config={"experiment": "003", "phase": "samples", "model": model,
                             "depth": DEPTH, "temperature": TEMP,
                             "difficulty": t.difficulty})
        ep.step(state_before=t.prompt, action=c.text, tokens_in=c.tokens_in,
                tokens_out=c.tokens_out, latency_ms=c.latency_ms,
                meta={"parsed": parsed, "format_ok": fmt_ok,
                      "correct": t.scored(c.text), "error": c.error})
        ep.finish(verdict=t.scored(c.text), outcome=parsed)
        w.write(ep)
        print(f"\r  samples {slug(model)} {i + 1}/{N}", end="", flush=True)
    print()


# Identical wording to 001's PEER_TEMPLATE. The peers differ; the prompt must not.
PEER_TEMPLATE = """{original}

Three assistants were asked the question above independently. Their full answers follow.

{peers}
Reconsider the question in light of these answers. They may all be wrong. Work through
the reporting chain yourself and count the levels. End your reply with a final line of
the form `ANSWER: <name>`."""


def phase_deliberate(model: str) -> None:
    b = require(model)
    j = PANEL.index(model)
    r1 = [round_one(m) for m in PANEL]
    w = TraceWriter(f"003_delib_{slug(model)}", results_dir=RUNS)
    for i, t in enumerate(tasks()):
        # Peers keep panel order and are labelled A/B/C, so an agent's position in the
        # list is fixed across the panel and cannot be confounded with its family.
        peers = "\n\n".join(f"Assistant {chr(65 + m)} said:\n{r1[m][t.task_id]['action']}"
                            for m in range(len(PANEL)) if m != j)
        prompt = PEER_TEMPLATE.format(original=t.prompt, peers=peers)
        c = b.complete(prompt, temperature=TEMP, max_tokens=MAX_TOK,
                       seed=t.seed * 10 + 100 + j)
        parsed, fmt_ok = t.parse(c.text)
        prior = r1[j][t.task_id]["meta"]["parsed"]
        ep = Episode(task_id=t.task_id, seed=t.seed,
                     config={"experiment": "003", "phase": "deliberate", "model": model,
                             "agent": j, "depth": DEPTH, "temperature": TEMP,
                             "difficulty": t.difficulty})
        ep.step(state_before=prompt, action=c.text, tokens_in=c.tokens_in,
                tokens_out=c.tokens_out, latency_ms=c.latency_ms,
                meta={"agent": j, "parsed": parsed, "format_ok": fmt_ok,
                      "correct": t.scored(c.text), "error": c.error,
                      "round1_parsed": prior,
                      "changed_mind": parsed.lower() != prior.lower()})
        ep.finish(verdict=t.scored(c.text), outcome=parsed)
        w.write(ep)
        print(f"\r  deliberate {slug(model)} {i + 1}/{N}", end="", flush=True)
    print()


def vote(answers: list[str]) -> str:
    """Majority, tie-broken toward the earliest panel member -- same rule as 001."""
    c = Counter(answers)
    top = max(c.values())
    return next(a for a in answers if c[a] == top)


def report() -> None:
    gold = {t.task_id: str(t.answer).lower() for t in tasks()}
    ids = sorted(gold)
    pre = {m: round_one(m) for m in PANEL}
    post = {}
    for m in PANEL:
        p = RUNS / f"003_delib_{slug(m)}.jsonl"
        if p.exists():
            post[m] = {e["task_id"]: e["steps"][0] for e in read(p)}

    print(f"\n003 -- mixed panel, multi_hop d={DEPTH}, temp={TEMP}, n={N}")
    print("     " + " / ".join(slug(m) for m in PANEL) + "\n")
    print(f"{'arm':<32} {'acc':>6}  {'95% CI':<13} {'tok_in':>8} {'tok_out':>8} {'total':>8}")

    def line(label, hits, ti, to):
        lo, hi = wilson(hits, len(ids))
        print(f"{label:<32} {hits / len(ids):>6.2f}  [{lo:.2f},{hi:.2f}]"
              f"  {ti:>8} {to:>8} {ti + to:>8}")

    for m in PANEL:                             # each family alone, for reference
        h = sum(pre[m][i]["meta"]["parsed"].lower() == gold[i] for i in ids)
        line(f"  solo: {slug(m)}", h,
             sum(pre[m][i]["tokens_in"] for i in ids),
             sum(pre[m][i]["tokens_out"] for i in ids))

    hits = sum(vote([pre[m][i]["meta"]["parsed"].lower() for m in PANEL]) == gold[i] for i in ids)
    line("C-mixed: k=3 vote, no comms", hits,
         sum(pre[m][i]["tokens_in"] for m in PANEL for i in ids),
         sum(pre[m][i]["tokens_out"] for m in PANEL for i in ids))

    if len(post) == len(PANEL):
        hits_d = sum(vote([post[m][i]["meta"]["parsed"].lower() for m in PANEL]) == gold[i]
                     for i in ids)
        line("D-mixed: k=3 + revision round", hits_d,
             sum(pre[m][i]["tokens_in"] for m in PANEL for i in ids)
             + sum(post[m][i]["tokens_in"] for m in PANEL for i in ids),
             sum(pre[m][i]["tokens_out"] for m in PANEL for i in ids)
             + sum(post[m][i]["tokens_out"] for m in PANEL for i in ids))

        ch = sum(post[m][i]["meta"]["changed_mind"] for m in PANEL for i in ids)
        print(f"\n  changed answer after seeing peers: {ch}/{len(PANEL) * len(ids)} "
              f"({ch / (len(PANEL) * len(ids)):.0%})   [001, single family: 50%]")

        for label, tab in (("pre", pre), ("post", post)):
            rows = {}
            for i in ids:
                ans = [tab[m][i]["meta"]["parsed"].lower() for m in PANEL]
                d = len(set(ans))
                r = rows.setdefault(d, [0, 0])
                r[0] += 1
                r[1] += vote(ans) == gold[i]
            print(f"  {label}-deliberation agreement:")
            for d in sorted(rows):
                n, c = rows[d]
                print(f"    {d} distinct: {n:3d} tasks, majority correct {c:3d}/{n:3d} = {c / n:.2f}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    if cmd == "report":
        report()
    else:
        arg = sys.argv[2]
        model = next(m for m in PANEL if slug(m) == arg or m == arg)
        {"samples": phase_samples, "deliberate": phase_deliberate}[cmd](model)
