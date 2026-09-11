"""010 -- can the deliberation curve be used, or only described?

008/009 say the revision delta tracks the fraction of peers that are correct. Nobody can
observe that at runtime. This asks whether any runtime-observable feature predicts it, and
whether gating on that feature would have improved a run that actually happened.

No new model calls. 001_deliberate and 004_deliberate each ran three qwen2.5 agents that
exchanged round-one answers; for any agent its peers are the other two agents' round-one
answers, and peer correctness is recoverable by scoring those against the stored gold. That
is 1,170 measured instances on *natural* blocks -- blocks whose peer correctness is
clustered by task difficulty, unlike 008's and 009's selected ones.

Usage:  uv run experiments/010-gating/run.py
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.trace import read                                    # noqa: E402

NATURAL = {
    "001": ROOT / "experiments/001-deliberation/runs/001_deliberate.jsonl",
    "004": ROOT / "experiments/004-prompt-ceiling/runs/004_deliberate.jsonl",
}
SELECTED = sorted((ROOT / "experiments/008-competence-gap/runs").glob("008_delib_*.jsonl")) \
    + sorted((ROOT / "experiments/009-panel-composition/runs").glob("009_delib_*.jsonl"))

FEATURES = ("agree_frac", "n_distinct", "peers_with_me", "unanimous", "consensus_with_me")
MIN_FIRE = 0.10          # a gate firing on under 10% of instances is not a result


def _feats(mine: str, peers: list[str]) -> dict[str, float]:
    """Everything an agent could compute from what it can see: the peers' answers and its
    own. Correctness never enters."""
    low = [p.lower() for p in peers]
    me = mine.lower()
    counts = Counter(low)
    modal = max(counts.values())
    return {
        "agree_frac": modal / len(low),
        "n_distinct": len(counts) / len(low),
        "peers_with_me": sum(1 for p in low if p == me) / len(low),
        "unanimous": float(len(counts) == 1),
        "consensus_with_me": float(len(counts) == 1 and low[0] == me),
    }


def natural_rows() -> dict[str, list[dict]]:
    """One row per (task, agent). Peers are the other agents' round-one answers."""
    out: dict[str, list[dict]] = {}
    for tag, path in NATURAL.items():
        rows = []
        for e in read(path):
            gold = (e.get("outcome") or "").lower()
            steps = e["steps"]
            r1 = [s["meta"]["round1_parsed"] for s in steps]
            for i, s in enumerate(steps):
                peers = [r1[j] for j in range(len(steps)) if j != i]
                peer_ok = [p.lower() == gold for p in peers]
                pre = r1[i].lower() == gold
                post = bool(s["meta"]["correct"])
                rows.append({"task": e["task_id"], "agent": i,
                             "frac_correct": sum(peer_ok) / len(peer_ok),
                             "delta": int(post) - int(pre),
                             **_feats(r1[i], peers)})
        out[tag] = rows
    return out


def selected_rows() -> list[dict]:
    rows = []
    for path in SELECTED:
        for e in read(path):
            m = e["steps"][0]["meta"]
            peers, ok = m["peer_parsed"], m["peer_correct"]
            rows.append({"task": e["task_id"],
                         "frac_correct": sum(bool(x) for x in ok) / len(ok),
                         "delta": int(bool(m["correct"])) - int(bool(m["round1_correct"])),
                         **_feats(m["round1_parsed"], peers)})
    return rows


def auc(scores: list[float], labels: list[int]) -> float:
    """Rank AUC with ties at half credit. Written out rather than imported so the number
    cannot silently change with a library version."""
    pos = [s for s, y in zip(scores, labels) if y]
    neg = [s for s, y in zip(scores, labels) if not y]
    if not pos or not neg:
        return float("nan")
    wins = sum((a > b) + 0.5 * (a == b) for a in pos for b in neg)
    return wins / (len(pos) * len(neg))


def _gate_value(rows: list[dict], feat: str, thr: float) -> tuple[float, float]:
    """Mean delta under 'deliberate iff feat >= thr', and the fire rate.

    Not deliberating is worth exactly 0 by construction: the agent keeps its round-one
    answer. So a gate's value is the mean of delta over fired instances, spread across all
    of them -- which is what makes a rarely-firing gate look good and why fire rate is
    returned alongside it."""
    fired = [r for r in rows if r[feat] >= thr]
    if not fired:
        return 0.0, 0.0
    return sum(r["delta"] for r in fired) / len(rows), len(fired) / len(rows)


def main() -> None:
    nat = natural_rows()
    allnat = [r for rs in nat.values() for r in rs]
    sel = selected_rows()

    print(f"010 -- gating. natural {len(allnat)} instances "
          f"({', '.join(f'{k} {len(v)}' for k, v in nat.items())}), "
          f"selected {len(sel)}\n")

    # --- H1/H4: does anything predict "most peers correct"? -------------------------
    print("  AUC for predicting 'most peers are correct' (frac_correct > 0.5)")
    print(f"    {'feature':18s} {'natural':>8s} {'selected':>9s}")
    for f in FEATURES:
        a = auc([r[f] for r in allnat], [r["frac_correct"] > 0.5 for r in allnat])
        b = auc([r[f] for r in sel], [r["frac_correct"] > 0.5 for r in sel])
        print(f"    {f:18s} {a:8.3f} {b:9.3f}")

    base = sum(r["delta"] for r in allnat) / len(allnat)
    print(f"\n  always deliberate on natural blocks: {base:+.3f}   "
          f"never deliberate: +0.000")

    # --- H2/H3: fit the threshold on one experiment, evaluate on the other ----------
    print("\n  gate value, threshold fitted on one experiment and evaluated on the other")
    print(f"    {'feature':18s} {'fit':>4s} {'thr':>5s} {'fit val':>8s} "
          f"{'eval val':>9s} {'eval fire':>10s} {'vs always':>10s}")
    for f in FEATURES:
        for fit_tag, eval_tag in (("001", "004"), ("004", "001")):
            cand = sorted({r[f] for r in nat[fit_tag]})
            best, bthr = None, None
            for thr in cand:
                v, fire = _gate_value(nat[fit_tag], f, thr)
                if fire >= MIN_FIRE and (best is None or v > best):
                    best, bthr = v, thr
            if bthr is None:
                continue
            ev, efire = _gate_value(nat[eval_tag], f, bthr)
            ebase = sum(r["delta"] for r in nat[eval_tag]) / len(nat[eval_tag])
            print(f"    {f:18s} {fit_tag:>4s} {bthr:5.2f} {best:+8.3f} "
                  f"{ev:+9.3f} {efire:10.2f} {ev - ebase:+10.3f}")

    # --- the shape of the thing being gated on -------------------------------------
    print("\n  measured delta by observed agreement, natural blocks")
    print(f"    {'agree_frac':>10s} {'peers_with_me':>13s} {'n':>5s} {'frac correct':>12s} "
          f"{'delta':>8s}")
    cells: dict[tuple[float, float], list[dict]] = {}
    for r in allnat:
        cells.setdefault((r["agree_frac"], r["peers_with_me"]), []).append(r)
    for key in sorted(cells):
        v = cells[key]
        print(f"    {key[0]:10.2f} {key[1]:13.2f} {len(v):5d} "
              f"{sum(x['frac_correct'] for x in v)/len(v):12.3f} "
              f"{sum(x['delta'] for x in v)/len(v):+8.3f}")


if __name__ == "__main__":
    main()
