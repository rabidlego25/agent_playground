"""001 -- does deliberation between agents beat one agent, at matched cost?

Two phases, run separately so the expensive one is done once:

  samples     k_max independent samples per task, no communication. Arm A is the k=1
              prefix and arm C at any k <= k_max is the k-prefix of the same draws, so
              the whole cost curve comes from one sweep instead of one sweep per k.
  deliberate  arm D. Reuses the first k samples from the `samples` phase as round one,
              shows each agent what the others said, and takes one revision round. D
              therefore shares its history with C rather than being an independent draw,
              which removes sampling noise from the contrast.

The comparison is cost-normalised: C is a curve of accuracy against total tokens and D
is a point. "Deliberation helps" means D lies above that curve, not that D beats C at
equal k -- equal k gives D a free extra round and is the usual way this gets overstated.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))

from _lab import require, wilson                      # noqa: E402
from lib.tasks import generate                        # noqa: E402
from lib.trace import Episode, TraceWriter, read      # noqa: E402

N, DEPTH, TEMP, K_MAX, K_DELIB = 195, 4, 0.7, 7, 3
MODEL = "ollama:qwen2.5"
SEED0 = 5000                     # same block as probe_self_consistency, so n=60 replays
MAX_TOK = 400


def tasks():
    return [generate("multi_hop", SEED0 + s, depth=DEPTH) for s in range(N)]


def phase_samples() -> None:
    b = require(MODEL)
    w = TraceWriter("001_samples", results_dir=Path(__file__).parent / "runs")
    for i, t in enumerate(tasks()):
        ep = Episode(task_id=t.task_id, seed=t.seed,
                     config={"experiment": "001", "phase": "samples", "arm": "A/C",
                             "model": MODEL, "k_max": K_MAX, "depth": DEPTH,
                             "temperature": TEMP, "difficulty": t.difficulty})
        for j in range(K_MAX):
            c = b.complete(t.prompt, temperature=TEMP, max_tokens=MAX_TOK,
                           seed=t.seed * 10 + j)
            parsed, fmt_ok = t.parse(c.text)
            ep.step(state_before=t.prompt, action=c.text, tokens_in=c.tokens_in,
                    tokens_out=c.tokens_out, latency_ms=c.latency_ms,
                    meta={"sample": j, "parsed": parsed, "format_ok": fmt_ok,
                          "correct": t.scored(c.text), "error": c.error})
        ep.finish(verdict=ep.steps[0].meta["correct"], outcome=ep.steps[0].meta["parsed"])
        w.write(ep)
        print(f"\r  samples {i + 1}/{N}", end="", flush=True)
    print()


PEER_TEMPLATE = """{original}

Three assistants were asked the question above independently. Their full answers follow.

{peers}
Reconsider the question in light of these answers. They may all be wrong. Work through
the reporting chain yourself and count the levels. End your reply with a final line of
the form `ANSWER: <name>`."""


def phase_deliberate() -> None:
    b = require(MODEL)
    src = {e["task_id"]: e for e in read(Path(__file__).parent / "runs" / "001_samples.jsonl")}
    w = TraceWriter("001_deliberate", results_dir=Path(__file__).parent / "runs")
    for i, t in enumerate(tasks()):
        prior = src.get(t.task_id)
        if prior is None:
            sys.exit(f"no round-one samples for {t.task_id}; run the samples phase first")
        round1 = prior["steps"][:K_DELIB]
        ep = Episode(task_id=t.task_id, seed=t.seed,
                     config={"experiment": "001", "phase": "deliberate", "arm": "D",
                             "model": MODEL, "k": K_DELIB, "depth": DEPTH,
                             "temperature": TEMP, "difficulty": t.difficulty,
                             "round1_run_id": prior["run_id"]})
        for j in range(K_DELIB):
            peers = "\n\n".join(
                f"Assistant {chr(65 + m)} said:\n{round1[m]['action']}"
                for m in range(K_DELIB) if m != j)
            prompt = PEER_TEMPLATE.format(original=t.prompt, peers=peers)
            c = b.complete(prompt, temperature=TEMP, max_tokens=MAX_TOK,
                           seed=t.seed * 10 + 100 + j)
            parsed, fmt_ok = t.parse(c.text)
            ep.step(state_before=prompt, action=c.text, tokens_in=c.tokens_in,
                    tokens_out=c.tokens_out, latency_ms=c.latency_ms,
                    meta={"agent": j, "parsed": parsed, "format_ok": fmt_ok,
                          "correct": t.scored(c.text), "error": c.error,
                          "round1_parsed": round1[j]["meta"]["parsed"],
                          "changed_mind": parsed.lower() != round1[j]["meta"]["parsed"].lower()})
        # arm D verdict: majority over the revised answers
        votes = Counter(s.meta["parsed"].lower() for s in ep.steps)
        won = votes.most_common(1)[0][0]
        gold = str(t.answer).lower()
        ep.finish(verdict=won == gold, outcome=won)
        w.write(ep)
        print(f"\r  deliberate {i + 1}/{N}", end="", flush=True)
    print()


BUDGET_TEMPLATE = """{original}

Work the reporting chain {k} separate times, independently. Label them Attempt 1
through Attempt {k}. Start each attempt from the fact list again and count the levels
from scratch -- do not let an earlier attempt decide a later one. Then give the answer
that most of your attempts agree on. End your reply with a final line of the form
`ANSWER: <name>`."""

B_KS = (3, 7)                    # matched to arm C's k, so the contrast is context sharing


def phase_budget() -> None:
    """Arm B: k derivations inside ONE context, vs arm C's k derivations in k contexts.

    Not 'a bigger token cap' -- that arm is dead on arrival. The 400-token cap in the
    samples phase bound 1 of 1365 completions (mean output 112 tokens), so raising it
    changes nothing. The model has to be asked to do more work, not permitted to.

    Holding the number of derivations fixed and varying only whether they share a context
    isolates the same variable as D vs C. If correlated error is what sinks D, B should
    sink with it.
    """
    b = require(MODEL)
    w = TraceWriter("001_budget", results_dir=Path(__file__).parent / "runs")
    for i, t in enumerate(tasks()):
        for k in B_KS:
            prompt = BUDGET_TEMPLATE.format(original=t.prompt, k=k)
            c = b.complete(prompt, temperature=TEMP, max_tokens=MAX_TOK * k,
                           seed=t.seed * 10 + 200 + k)
            parsed, fmt_ok = t.parse(c.text)
            ep = Episode(task_id=t.task_id, seed=t.seed,
                         config={"experiment": "001", "phase": "budget", "arm": f"B{k}",
                                 "model": MODEL, "k": k, "depth": DEPTH,
                                 "temperature": TEMP, "max_tokens": MAX_TOK * k,
                                 "difficulty": t.difficulty})
            ep.step(state_before=prompt, action=c.text, tokens_in=c.tokens_in,
                    tokens_out=c.tokens_out, latency_ms=c.latency_ms,
                    meta={"k": k, "parsed": parsed, "format_ok": fmt_ok,
                          "correct": t.scored(c.text), "error": c.error})
            ep.finish(verdict=t.scored(c.text), outcome=parsed)
            w.write(ep)
        print(f"\r  budget {i + 1}/{N}", end="", flush=True)
    print()


def report() -> None:
    runs = Path(__file__).parent / "runs"
    S = read(runs / "001_samples.jsonl")
    gold = {t.task_id: str(t.answer).lower() for t in tasks()}
    print(f"\n001 -- multi_hop d={DEPTH}, temp={TEMP}, {MODEL}, n={len(S)}\n")
    print(f"{'arm':<28} {'acc':>6}  {'95% CI':<13} {'tok_in':>8} {'tok_out':>8} {'total':>8}")
    rows = []
    for k in (1, 3, 5, 7):
        hits = ti = to = 0
        for e in S:
            steps = e["steps"][:k]
            votes = Counter(s["meta"]["parsed"].lower() for s in steps)
            top = max(votes.values())
            # tie-break toward the earliest sample, matching lib majority()
            won = next(s["meta"]["parsed"].lower() for s in steps if votes[s["meta"]["parsed"].lower()] == top)
            hits += won == gold[e["task_id"]]
            ti += sum(s["tokens_in"] for s in steps)
            to += sum(s["tokens_out"] for s in steps)
        lo, hi = wilson(hits, len(S))
        label = "A: single sample" if k == 1 else f"C: k={k} majority, no comms"
        rows.append((label, hits / len(S), lo, hi, ti, to, ti + to))
    dpath = runs / "001_deliberate.jsonl"
    if dpath.exists():
        D = read(dpath)
        hits = sum(bool(e["verdict"]) for e in D)
        # D's true cost includes the round-one samples it reused
        r1_in = sum(sum(s["tokens_in"] for s in e["steps"][:K_DELIB]) for e in S)
        r1_out = sum(sum(s["tokens_out"] for s in e["steps"][:K_DELIB]) for e in S)
        ti = r1_in + sum(e["tokens_in_total"] for e in D)
        to = r1_out + sum(e["tokens_out_total"] for e in D)
        lo, hi = wilson(hits, len(D))
        rows.append((f"D: k={K_DELIB} + 1 revision round", hits / len(D), lo, hi, ti, to, ti + to))
        changed = sum(s["meta"]["changed_mind"] for e in D for s in e["steps"])
        total = sum(len(e["steps"]) for e in D)
        print()
    for lab, acc, lo, hi, ti, to, tot in rows:
        print(f"{lab:<28} {acc:>6.2f}  [{lo:.2f},{hi:.2f}]  {ti:>8} {to:>8} {tot:>8}")
    bpath = runs / "001_budget.jsonl"
    if bpath.exists():
        B = read(bpath)
        for k in B_KS:
            arm = [e for e in B if e["config"]["k"] == k]
            if not arm:
                continue
            hits = sum(bool(e["verdict"]) for e in arm)
            lo, hi = wilson(hits, len(arm))
            ti = sum(e["tokens_in_total"] for e in arm)
            to = sum(e["tokens_out_total"] for e in arm)
            print(f"{f'B: k={k} in one context':<28} {hits / len(arm):>6.2f}  "
                  f"[{lo:.2f},{hi:.2f}]  {ti:>8} {to:>8} {ti + to:>8}")
    if dpath.exists():
        print(f"\n  agents that changed their answer after seeing peers: {changed}/{total}"
              f" ({changed / total:.0%})")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    {"samples": phase_samples, "deliberate": phase_deliberate,
     "budget": phase_budget, "report": report}[cmd]()
