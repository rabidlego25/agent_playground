"""009 -- is deliberation harm set by P(no correct peer), or by mean peer competence?

008 found the delta depends on k, the number of correct peers, with per-k constants that
were identical across five conditions. But every one of those conditions used **two i.i.d.
peers**, so the note's closing claim -- that the composition statistic is max(member
accuracy) rather than mean -- was an extrapolation, not a measurement.

Three peers, three compositions, two comparisons that cut opposite ways:

  U33  (0.33, 0.33, 0.33)   mean 0.333  max 0.33  P(k=0)=0.296
  S33  (1.00, 0.00, 0.00)   mean 0.333  max 1.00  P(k=0)=0.000
  S67  (1.00, 0.50, 0.50)   mean 0.667  max 1.00  P(k=0)=0.000

U33 vs S33 holds the mean and moves the max; S33 vs S67 holds the max and moves the mean.

  deliberate <condition>   qwen's revision on that condition's peer blocks
  report                   deltas, McNemar, per-k decomposition, and the out-of-sample
                           test of 008's constants

See README.md for the predictions, committed before any call.

Usage:  uv run experiments/009-panel-composition/run.py deliberate U33 | report
"""
from __future__ import annotations

import random
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from _lab import mcnemar, wilson                       # noqa: E402
from lib.models import get                            # noqa: E402
from lib.trace import Episode, TraceWriter, read      # noqa: E402

TEMP, MAX_TOK = 0.7, 800        # identical to 004/005/008
MODEL = "ollama:qwen2.5"
N_PEERS = 3                     # two peers cannot vary composition
SEED_DELIB = 900                # disjoint from 004 (+400+j), 005 (500), 008 (800)

HERE = Path(__file__).parent
RUNS = HERE / "runs"
EIGHT = ROOT / "experiments" / "008-competence-gap" / "run.py"

# Per-peer accuracies. Order within a block is shuffled before rendering -- S33's strong
# member would otherwise always be Assistant A, and a positional regularity the subject
# could pick up would confound every comparison here.
CONDITIONS: dict[str, tuple[float, ...]] = {
    "U33": (1 / 3, 1 / 3, 1 / 3),
    "S33": (1.00, 0.00, 0.00),
    "S67": (1.00, 0.50, 0.50),
}
ANCHOR = "U33"                  # the uniform panel the others are compared against

# 008's pooled per-k deltas, for the out-of-sample check in report(). k=3 was never
# observed by 008; treating it as k=2 is an assumption and is flagged in the README.
EIGHT_PER_K = {0: -0.448, 1: -0.011, 2: 0.202, 3: 0.202}


def _from_008(name: str):
    """Load 008's task pool and peer template rather than copying them, so the two
    experiments cannot drift apart. Same mechanism 004/005/008 use to load 001."""
    ns: dict = {"__file__": str(EIGHT), "__name__": "_experiment_008"}
    exec(compile(EIGHT.read_text(), str(EIGHT), "exec"), ns)      # noqa: S102
    return ns[name]


pool = _from_008("pool")
tasks = _from_008("tasks")
PEER_TEMPLATE = _from_008("PEER_TEMPLATE")


def peer_block(entry: dict, accs: tuple[float, ...],
               rng: random.Random) -> list[dict]:
    """One peer per accuracy, then shuffled.

    Each peer is independently correct with its own probability, drawn from this task's
    real draws -- so every peer answer is a genuine model output with real reasoning, as
    in 008. The shuffle is what makes the composition non-positional."""
    peers = [rng.choice(entry["right"] if rng.random() < a else entry["wrong"])
             for a in accs]
    rng.shuffle(peers)
    return peers


def _done(stem: str) -> set[str]:
    path = RUNS / f"{stem}.jsonl"
    return {e["task_id"] for e in read(path)} if path.exists() else set()


def deliberate(cond: str) -> None:
    accs = CONDITIONS[cond]
    entries, ts = pool(), {t.task_id: t for t in tasks()}
    RUNS.mkdir(exist_ok=True)
    stem = f"009_delib_{cond}"
    done = _done(stem)
    todo = [tid for tid in entries if tid not in done]
    print(f"{cond}: peers {tuple(round(a, 2) for a in accs)}, mean {sum(accs)/len(accs):.3f}, "
          f"{len(entries)} tasks, {len(todo)} to do")

    b = get(MODEL)
    with TraceWriter(stem, results_dir=RUNS) as w:
        for i, tid in enumerate(todo, 1):
            entry, t = entries[tid], ts[tid]
            # zlib.crc32, not hash(): Python randomises string hashing per
            # process, so hash()-seeded blocks cannot be regenerated and a
            # resumed run mixes draws from two different seeds.
            rng = random.Random(zlib.crc32(f"{tid}|{cond}|009".encode()))
            peers = peer_block(entry, accs, rng)
            text = "\n\n".join(f"Assistant {chr(65 + j)} said:\n{pr['action']}"
                               for j, pr in enumerate(peers))
            c = b.complete(PEER_TEMPLATE.format(original=t.prompt, peers=text),
                           temperature=TEMP, max_tokens=MAX_TOK,
                           seed=t.seed * 10 + SEED_DELIB)
            parsed, fmt_ok = t.parse(c.text)
            prior = entry["subject"]["meta"]["parsed"]
            peer_answers = [pr["meta"]["parsed"] for pr in peers]
            peer_correct = [bool(pr["meta"]["correct"]) for pr in peers]
            low = parsed.lower()
            changed = low != prior.lower()
            ep = Episode(task_id=tid, seed=t.seed,
                         config={"experiment": "009", "condition": cond,
                                 "peer_accuracies": list(accs), "model": MODEL,
                                 "prompt": "B1n", "n_peers": N_PEERS})
            ep.step(state_before=None, action=c.text,
                    tokens_in=c.tokens_in, tokens_out=c.tokens_out,
                    latency_ms=c.latency_ms,
                    meta={"parsed": parsed, "format_ok": fmt_ok,
                          "correct": t.scored(c.text),
                          "round1_parsed": prior,
                          "round1_correct": entry["subject"]["meta"]["correct"],
                          "peer_parsed": peer_answers,
                          "peer_correct": peer_correct,
                          # k is the variable 008 says everything depends on; recorded
                          # explicitly rather than recomputed from peer_correct later.
                          "k_correct": sum(peer_correct),
                          "changed_mind": changed,
                          "adopted_peer": changed and low in [a.lower() for a in peer_answers],
                          "cap_bound": c.tokens_out >= MAX_TOK})
            w.write(ep.finish(verdict=t.scored(c.text), outcome=parsed))
            if i % 20 == 0 or i == len(todo):
                print(f"  {i}/{len(todo)}")


def report() -> None:
    entries = pool()
    base = {tid: e["subject"]["meta"]["correct"] for tid, e in entries.items()}
    solo = sum(base.values()) / len(base)
    print(f"009 -- panel composition. n={len(base)} tasks, subject solo {solo:.3f}\n")
    print(f"  {'cond':5s} {'mean':>5s} {'max':>5s} {'realised':>8s} {'P(k=0)':>7s} "
          f"{'revised':>8s} {'delta':>7s} {'95% CI':>16s} {'w->r':>5s} {'r->w':>5s}")

    rows, per_k = {}, {}
    for cond, accs in CONDITIONS.items():
        path = RUNS / f"009_delib_{cond}.jsonl"
        if not path.exists():
            continue
        eps = {e["task_id"]: e for e in read(path)}
        ids = [t for t in base if t in eps]
        metas = [eps[t]["steps"][0]["meta"] for t in ids]
        post = [m["correct"] for m in metas]
        pre = [base[t] for t in ids]
        ks = [m["k_correct"] for m in metas]
        wr = sum(1 for a, bb in zip(pre, post) if not a and bb)
        rw = sum(1 for a, bb in zip(pre, post) if a and not bb)
        d = (sum(post) - sum(pre)) / len(ids)
        lo, hi = wilson(sum(post), len(ids))
        # Realised mean peer accuracy: the conditions are matched by design, and a drift
        # between them would confound the comparison rather than test it.
        realised = sum(sum(m["peer_correct"]) for m in metas) / (len(ids) * N_PEERS)
        rows[cond] = (ids, pre, post, d, ks)
        for k, a, bb in zip(ks, pre, post):
            per_k.setdefault(k, []).append(bb - a)
        print(f"  {cond:5s} {sum(accs)/len(accs):5.2f} {max(accs):5.2f} {realised:8.3f} "
              f"{ks.count(0)/len(ks):7.3f} {sum(post)/len(ids):8.3f} {d:+7.3f} "
              f"[{lo:.3f}, {hi:.3f}] {wr:5d} {rw:5d}")

    if ANCHOR in rows:
        print(f"\n  exact McNemar against {ANCHOR}:")
        aids, _, apost, _, _ = rows[ANCHOR]
        amap = dict(zip(aids, apost))
        for cond, (ids, _, post, _, _) in rows.items():
            if cond == ANCHOR:
                continue
            shared = [t for t in ids if t in amap]
            x = [amap[t] for t in shared]
            y = [post[shared.index(t)] for t in shared]
            a_only, b_only, pv = mcnemar(x, y)
            print(f"    {ANCHOR} vs {cond:4s}  discordant {a_only}/{b_only}  p={pv:.4f}")

    if per_k:
        print("\n  per-k delta measured here, against 008's constants:")
        print(f"    {'k':>2s} {'n':>4s} {'009':>8s} {'008':>8s} {'diff':>8s}")
        for k in sorted(per_k):
            v = per_k[k]
            e8 = EIGHT_PER_K.get(k)
            got = sum(v) / len(v)
            print(f"    {k:2d} {len(v):4d} {got:+8.3f} {e8:+8.3f} {got - e8:+8.3f}"
                  + ("   (008 never observed k=3)" if k == 3 else ""))

        print("\n  out-of-sample: each condition's aggregate from its own P(k) x 008's "
              "constants")
        print(f"    {'cond':5s} {'predicted':>10s} {'actual':>8s} {'resid':>7s}")
        for cond, (ids, _, _, d, ks) in rows.items():
            pred = sum(EIGHT_PER_K[k] for k in ks) / len(ks)
            print(f"    {cond:5s} {pred:+10.3f} {d:+8.3f} {d - pred:+7.3f}")

    if "S33" in rows and ANCHOR in rows:
        print(f"\n  H1 matched mean, max differs : S33-U33 = "
              f"{rows['S33'][3] - rows[ANCHOR][3]:+.3f}  (predicted +0.074, floor 0.050)")
    if "S67" in rows and "S33" in rows:
        print(f"  H2 matched max,  mean differs: S67-S33 = "
              f"{rows['S67'][3] - rows['S33'][3]:+.3f}  (predicted +0.160)")
    print("\n  Run-to-run noise floor on single calls is 0.050 "
          "(tests/probe_variance_floor.py); any delta has to clear it.")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    if cmd == "deliberate":
        which = sys.argv[2] if len(sys.argv) > 2 else None
        for c in ([which] if which else list(CONDITIONS)):
            deliberate(c)
    else:
        report()
