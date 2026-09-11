"""008 -- does deliberation harm track the competence gap, or family mismatch?

005 measured qwen2.5 losing 0.123 to deliberation against peers 0.43 below it, but those
peers were also a different model family. 004 measured net exactly zero against peers of
its own family at the same prompt. Two points, two things changed at once.

This holds family fixed and moves only the gap, using qwen's own draws as the peers:
`004_samples.jsonl` has 7 independent draws per task at B1n, each scored, so peer accuracy
is a knob and every peer answer is a real model output with real reasoning.

  deliberate <condition>   qwen's revision on that condition's peer blocks
  report                   deltas per condition, McNemar against the P65 anchor, adoption

The subject's round-one answer is draw 0 in every condition and is never re-run, so the
only thing that varies across conditions is peer competence and the comparison is paired
on task. See README.md for the predictions, committed before any call.

Usage:  uv run experiments/008-competence-gap/run.py deliberate P15 | report
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from _lab import mcnemar, wilson                       # noqa: E402
from lib.models import get                            # noqa: E402
from lib.tasks import generate                        # noqa: E402
from lib.trace import Episode, TraceWriter, read      # noqa: E402

N, DEPTH, TEMP, MAX_TOK = 195, 4, 0.7, 800     # identical to 004/005
SEED0 = 5000
SEED_DELIB = 800                # disjoint from 004 (+400+j) and 005 (500)
MODEL = "ollama:qwen2.5"
N_PEERS = 2                     # the structure qwen faced in 003 and 005

HERE = Path(__file__).parent
RUNS = HERE / "runs"
ONE = ROOT / "experiments" / "001-deliberation"
FOUR = ROOT / "experiments" / "004-prompt-ceiling" / "runs"

# peer accuracy per condition; subject solo on the retained set is 0.647
CONDITIONS = {"P100": 1.00, "P80": 0.80, "P65": 0.65, "P40": 0.40, "P15": 0.15}
ANCHOR = "P65"                  # the 004 replication point: peers at the subject's own level


def _prompt_from_001(name: str) -> str:
    """Load the peer template out of 001 rather than copying it, so 001/003/004/005/008
    cannot drift apart silently. Same mechanism 004 and 005 use."""
    src = ONE / "run.py"
    ns: dict = {"__file__": str(src), "__name__": "_experiment_001"}
    exec(compile(src.read_text(), str(src), "exec"), ns)          # noqa: S102
    return ns[name]


PEER_TEMPLATE = _prompt_from_001("PEER_TEMPLATE")


def tasks():
    return [generate("multi_hop", SEED0 + s, depth=DEPTH) for s in range(N)]


def pool() -> dict[str, dict]:
    """Per task: the subject's round-one draw and the correct/incorrect draws available
    as peers. Restricted to tasks where draws 1-6 hold both, so peer accuracy is dialable
    from 0 to 1 on every task in the set rather than on a condition-dependent subset --
    otherwise the task set would differ between conditions and the pairing would be a lie.
    """
    out = {}
    for e in read(FOUR / "004_samples.jsonl"):
        subject, rest = e["steps"][0], e["steps"][1:]
        right = [s for s in rest if s["meta"]["correct"]]
        wrong = [s for s in rest if not s["meta"]["correct"]]
        if not right or not wrong:
            continue
        out[e["task_id"]] = {"subject": subject, "right": right, "wrong": wrong,
                             "gold": e["outcome"]}
    return out


def peer_block(entry: dict, p: float, rng: random.Random) -> list[dict]:
    """Two peers whose expected accuracy is `p`, drawn from this task's real draws.

    Each peer is independently correct with probability p. Sampling per peer rather than
    fixing a count keeps peer accuracy a property of the condition instead of an exact
    quota, which would make the two peers' correctness anti-correlated within a task and
    quietly change what the subject sees."""
    return [rng.choice(entry["right"] if rng.random() < p else entry["wrong"])
            for _ in range(N_PEERS)]


def _done(stem: str) -> set[str]:
    """task_ids already written. TraceWriter is append-only, so a phase that dies partway
    cannot simply be re-run; skipping finished ids makes it idempotent and costs at most
    the task in flight. Taken from 005, which needed it."""
    path = RUNS / f"{stem}.jsonl"
    return {e["task_id"] for e in read(path)} if path.exists() else set()


def deliberate(cond: str) -> None:
    p = CONDITIONS[cond]
    entries, ts = pool(), {t.task_id: t for t in tasks()}
    RUNS.mkdir(exist_ok=True)
    stem = f"008_delib_{cond}"
    done = _done(stem)
    todo = [tid for tid in entries if tid not in done]
    print(f"{cond}: peer accuracy {p:.2f}, {len(entries)} tasks, {len(todo)} to do")

    b = get(MODEL)
    with TraceWriter(stem, results_dir=RUNS) as w:
        for i, tid in enumerate(todo, 1):
            entry, t = entries[tid], ts[tid]
            # Seeded per task and condition: the peer block is reproducible from the
            # trace, and two conditions never draw the same peers by accident.
            rng = random.Random(hash((tid, cond)) & 0xFFFFFFFF)
            peers = peer_block(entry, p, rng)
            text = "\n\n".join(f"Assistant {chr(65 + j)} said:\n{pr['action']}"
                               for j, pr in enumerate(peers))
            c = b.complete(PEER_TEMPLATE.format(original=t.prompt, peers=text),
                           temperature=TEMP, max_tokens=MAX_TOK,
                           seed=t.seed * 10 + SEED_DELIB)
            parsed, fmt_ok = t.parse(c.text)
            prior = entry["subject"]["meta"]["parsed"]
            peer_answers = [pr["meta"]["parsed"] for pr in peers]
            # Case-insensitive, matching 004 and 005. Comparing raw strings would count a
            # capitalisation difference as changing its mind and inflate the rate.
            low = parsed.lower()
            changed = low != prior.lower()
            ep = Episode(task_id=tid, seed=t.seed,
                         config={"experiment": "008", "condition": cond,
                                 "peer_accuracy": p, "model": MODEL, "prompt": "B1n",
                                 "n_peers": N_PEERS})
            ep.step(state_before=None, action=c.text,
                    tokens_in=c.tokens_in, tokens_out=c.tokens_out,
                    latency_ms=c.latency_ms,
                    meta={"parsed": parsed, "format_ok": fmt_ok,
                          # t.scored(), not string equality: the task's own scorer is what
                          # 004 and 005 used, and 001's oracle bug is what happens when a
                          # run invents its own comparison.
                          "correct": t.scored(c.text),
                          "round1_parsed": prior,
                          "round1_correct": entry["subject"]["meta"]["correct"],
                          "peer_parsed": peer_answers,
                          "peer_correct": [pr["meta"]["correct"] for pr in peers],
                          # kept apart deliberately: 005 logged only changed_mind and
                          # could not be compared with 003's adoption rate afterwards
                          "changed_mind": changed,
                          "adopted_peer": changed and low in [a.lower() for a in peer_answers],
                          "wrong_answers_available": len(entry["wrong"]),
                          "cap_bound": c.tokens_out >= MAX_TOK})
            w.write(ep.finish(verdict=t.scored(c.text), outcome=parsed))
            if i % 20 == 0 or i == len(todo):
                print(f"  {i}/{len(todo)}")


def report() -> None:
    entries = pool()
    base = {tid: e["subject"]["meta"]["correct"] for tid, e in entries.items()}
    solo = sum(base.values()) / len(base)
    print(f"008 -- competence gap. n={len(base)} tasks, subject solo {solo:.3f}\n")
    print(f"  {'cond':6s} {'peer acc':>8s} {'gap':>7s} {'revised':>8s} {'delta':>7s} "
          f"{'95% CI':>16s} {'w->r':>5s} {'r->w':>5s} {'chg':>5s} {'adopt':>6s}")

    rows = {}
    for cond, p in CONDITIONS.items():
        path = RUNS / f"008_delib_{cond}.jsonl"
        if not path.exists():
            continue
        eps = {e["task_id"]: e for e in read(path)}
        ids = [t for t in base if t in eps]
        post = [eps[t]["steps"][0]["meta"]["correct"] for t in ids]
        pre = [base[t] for t in ids]
        wr = sum(1 for a, bb in zip(pre, post) if not a and bb)
        rw = sum(1 for a, bb in zip(pre, post) if a and not bb)
        d = (sum(post) - sum(pre)) / len(ids)
        lo, hi = wilson(sum(post), len(ids))
        chg = sum(eps[t]["steps"][0]["meta"]["changed_mind"] for t in ids) / len(ids)
        ado = sum(eps[t]["steps"][0]["meta"]["adopted_peer"] for t in ids) / len(ids)
        rows[cond] = (ids, pre, post, d)
        print(f"  {cond:6s} {p:8.2f} {p - solo:+7.2f} {sum(post)/len(ids):8.3f} "
              f"{d:+7.3f} [{lo:.3f}, {hi:.3f}] {wr:5d} {rw:5d} {chg:5.2f} {ado:6.2f}")

    if ANCHOR in rows:
        print(f"\n  exact McNemar against {ANCHOR} (peers at the subject's own level):")
        aids, _, apost, _ = rows[ANCHOR]
        amap = dict(zip(aids, apost))
        for cond, (ids, _, post, _) in rows.items():
            if cond == ANCHOR:
                continue
            shared = [t for t in ids if t in amap]
            x = [amap[t] for t in shared]
            y = [post[shared.index(t)] for t in shared]
            a_only, b_only, pv = mcnemar(x, y)
            print(f"    {ANCHOR} vs {cond:5s}  discordant {a_only}/{b_only}  p={pv:.4f}")

    decompose()

    print("\n  Predictions from README.md, committed before the run:")
    print("    H1 delta declines monotonically P100 -> P15")
    print("    H2 delta at P15 <= -0.10  (gap-driven)  vs  > -0.05  (family-driven)")
    print("    H3 delta at P100 >= +0.10")
    print(f"\n  Run-to-run noise floor on single calls is 0.050 "
          f"(tests/probe_variance_floor.py); any delta has to clear it.")


def decompose() -> None:
    """The aggregate delta is a mixture: P(k correct peers) x delta given k.

    If delta-given-k is the same in every condition, then peer accuracy does nothing
    except move the mixture, and the causal variable is k rather than the gap. That is
    a strictly stronger claim than the headline curve, and it is the one this prints.
    """
    per = {}
    for cond in CONDITIONS:
        path = RUNS / f"008_delib_{cond}.jsonl"
        if not path.exists():
            continue
        d: dict[int, list[int]] = {}
        for e in read(path):
            m = e["steps"][0]["meta"]
            d.setdefault(sum(m["peer_correct"]), []).append(
                m["correct"] - m["round1_correct"])
        per[cond] = d
    if not per:
        return

    pooled: dict[int, list[int]] = {}
    for d in per.values():
        for k, v in d.items():
            pooled.setdefault(k, []).extend(v)
    pk = {k: sum(v) / len(v) for k, v in pooled.items()}

    print("\n  delta by number of correct peers, per condition")
    print("    k  " + "  ".join(f"{c:>13s}" for c in per))
    for k in sorted(pooled):
        cells = []
        for cond in per:
            v = per[cond].get(k)
            cells.append(f"{len(v):3d} {sum(v)/len(v):+7.3f}" if v else " " * 11)
        print(f"    {k}  " + "  ".join(f"{c:>13s}" for c in cells))
    print("    pooled  " + "  ".join(
        f"k={k}: {pk[k]:+.3f} (n={len(pooled[k])})" for k in sorted(pk)))

    # Reconstruct each condition's aggregate from the pooled per-k deltas and that
    # condition's mixture alone. A residual inside the 0.050 noise floor means peer
    # accuracy is fully mediated by P(k).
    print("\n  aggregate reconstructed from P(k) x pooled delta(k)")
    print(f"    {'cond':6s} {'P(0)':>6s} {'P(1)':>6s} {'P(2)':>6s} "
          f"{'predicted':>10s} {'actual':>8s} {'resid':>7s}")
    for cond, d in per.items():
        n = sum(len(v) for v in d.values())
        sh = {k: len(d.get(k, [])) / n for k in sorted(pk)}
        pred = sum(sh[k] * pk[k] for k in sorted(pk))
        act = sum(sum(v) for v in d.values()) / n
        print(f"    {cond:6s} {sh.get(0,0):6.2f} {sh.get(1,0):6.2f} {sh.get(2,0):6.2f} "
              f"{pred:+10.3f} {act:+8.3f} {act - pred:+7.3f}")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    if cmd == "deliberate":
        which = sys.argv[2] if len(sys.argv) > 2 else None
        for c in ([which] if which else list(CONDITIONS)):
            deliberate(c)
    else:
        report()
