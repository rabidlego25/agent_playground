"""k=3 independent samples with majority vote, against a single sample.

This is arm C vs arm A of experiment 001, run before any deliberation machinery exists.
Whatever ensembling alone buys is the bar communication has to clear -- if D never beats
this, the gain was never communication.
"""
from _lab import Cell, majority, require, table, wilson
from lib.tasks import Task, generate
from lib.trace import Episode, TraceWriter

N, K, DEPTH, TEMP, MODEL = 60, 3, 4, 0.7, "ollama:qwen2.5"

if __name__ == "__main__":
    b = require(MODEL)
    w = TraceWriter("probe_self_consistency")
    tasks = [generate("multi_hop", 5000 + s, depth=DEPTH) for s in range(N)]
    single = Cell("single sample (A)", {"arm": "A"})
    vote = Cell(f"k={K} majority, no comms (C)", {"arm": "C"})

    for t in tasks:
        answers, fmts, ep = [], [], Episode(task_id=t.task_id, seed=t.seed,
                                  config={"probe": "self_consistency", "model": MODEL,
                                          "k": K, "depth": DEPTH, "temperature": TEMP})
        for j in range(K):
            c = b.complete(t.prompt, temperature=TEMP, max_tokens=400, seed=t.seed * 10 + j)
            parsed, fmt_ok = t.parse(c.text)
            ep.step(state_before=t.prompt, action=c.text, tokens_in=c.tokens_in,
                    tokens_out=c.tokens_out, latency_ms=c.latency_ms,
                    meta={"sample": j, "parsed": parsed, "format_ok": fmt_ok,
                          "correct": t.scored(c.text), "error": c.error})
            answers.append(c.text)
            fmts.append(fmt_ok)
            if j == 0:                       # first sample IS the single-sample arm
                single.n += 1
                single.hits += int(t.scored(c.text))
                single.fmt_ok += int(t.parse(c.text)[1])
                single.tokens_out += c.tokens_out
                single.latency_ms += c.latency_ms
            vote.tokens_out += c.tokens_out
            vote.latency_ms += c.latency_ms
        won = majority(answers)
        ok = t.scored(won)
        vote.n += 1
        vote.hits += int(ok)
        vote.fmt_ok += int(all(fmts))       # fmt column for the vote arm = all k complied
        ep.finish(verdict=ok, outcome=won)
        w.write(ep)
        print(f"\r  {vote.n}/{N} tasks", end="", flush=True)
    print()
    print(table([single, vote], f"Self-consistency -- depth={DEPTH}, temp={TEMP}, {MODEL}, n={N}"))
    print(f"\n  Ensembling buys {vote.acc - single.acc:+.3f} accuracy for "
          f"{vote.tokens_out / max(single.tokens_out, 1):.1f}x the output tokens.")
