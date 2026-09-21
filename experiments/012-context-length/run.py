"""012 -- what does a longer context cost, in speed and in accuracy?

The roster has been running at ollama's default 4096-token window since the project
started: `lib/models.py` never set `num_ctx`, so llama3.1's advertised 131072 was served
at 1/32 of it and every local model sat at the same 4096 regardless of its card
(measured 2026-09-21). Raising it is one line. What it buys, and what it costs, is not.

Two things are conflated by the phrase "raise the context" and they are separated here:

  allocation  how large a KV cache is reserved (`num_ctx`). Costs memory at load.
  occupancy   how many tokens the prompt actually spends. Costs prefill, every call.

So `num_ctx` is held at 32768 for every cell except the anchor, and only the prompt grows.
The one variable is occupancy. The anchor (num_ctx=4096, no padding) is the configuration
every earlier result in this repo was produced under, and the 32768/no-padding cell is the
allocation control: if it differs from the anchor, reserving the window costs something on
its own, before a single extra token is read.

The reasoning task is byte-identical in all six cells -- same seeds, same depth, same
distractors. What grows is neutral filler prose placed *before* it, so any accuracy
difference is attributable to prompt length and not to task difficulty.

  run     the six cells, n=20 paired instances
  report  accuracy against the anchor (McNemar, paired), and the speed decomposition

Seeds are 2000..2019 at depth 3 / 6 distractors, which is the same block
`tests/probe_distractor_load.py` measured at 0.88 (n=50) -- so the anchor cell is also a
replication check on an existing number, not just a baseline for this experiment.
"""
from __future__ import annotations

import argparse
import random
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from _lab import mcnemar, run_cell, table, wilson      # noqa: E402
from lib.models import Ollama                          # noqa: E402
from lib.tasks import generate                         # noqa: E402
from lib.trace import TraceWriter, read                # noqa: E402

EXPERIMENT = "012_context"
MODEL = "qwen2.5:latest"
N, DEPTH, DISTRACTORS, SEED0 = 20, 3, 6, 2000
TEMP, MAX_TOK = 0.0, 400
TIMEOUT = 900                    # the 27k cell prefills for ~171s; 180s would abort it

# (label, num_ctx, padding target in tokens). Allocation is constant except for the anchor.
CELLS: list[tuple[str, int, int]] = [
    ("anchor-4k/pad0",   4096, 0),       # what every prior result in this repo ran under
    ("ctx32k/pad0",     32768, 0),       # allocation control: window reserved, not used
    ("ctx32k/pad2k",    32768, 2_000),
    ("ctx32k/pad6k",    32768, 6_000),
    ("ctx32k/pad14k",   32768, 14_000),
    ("ctx32k/pad27k",   32768, 27_000),
]
ANCHOR = CELLS[0][0]

# ------------------------------------------------------------------ filler
# Neutral prose. Three constraints, each load-bearing:
#   1. no personal names, so it cannot be mistaken for a fact about the chain;
#   2. none of the task's relational vocabulary -- "reports", "above", "level", "manager";
#   3. varied rather than one sentence repeated, because a model attending over 27k tokens
#      of an identical repeated block is not a model attending over 27k tokens of text.
_ART = ["crate", "pallet", "logbook", "ledger", "bin", "carton", "spool", "canister",
        "drum", "tray", "reel", "folder", "envelope", "cylinder", "sack", "flask"]
_PLACE = ["the north aisle", "bay 14", "the cold room", "the mezzanine", "dock 3",
          "the annex", "the overflow shelf", "the sorting table", "the loading yard",
          "the long corridor", "the back stair", "the transit cage"]
_ACT = ["was counted", "was resealed", "was relabelled", "was weighed", "was moved",
        "was logged", "was set aside", "was inspected", "was stacked", "was tagged"]
_WHEN = ["on the second pass", "before the shift change", "during the quarterly audit",
         "after the delivery window closed", "at the start of the cycle",
         "once the manifest cleared", "between the two inventories"]
_TAIL = ["and the count matched the sheet", "and the discrepancy was noted in the margin",
         "and nothing further was recorded", "and the seal was left intact",
         "and the entry was initialled twice", "and the weight was carried forward",
         "and the reference number was copied over"]


def _sentence(rng: random.Random) -> str:
    return (f"The {rng.choice(_ART)} in {rng.choice(_PLACE)} {rng.choice(_ACT)} "
            f"{rng.choice(_WHEN)}, {rng.choice(_TAIL)}.")


def filler(target_tokens: int, rng: random.Random, chars_per_token: float) -> str:
    """Prose of approximately `target_tokens` tokens. The target is approximate by
    construction; the x-axis of this experiment is the *measured* `tokens_in` on each
    call, which the trace records, never this number."""
    if target_tokens <= 0:
        return ""
    want = int(target_tokens * chars_per_token)
    out: list[str] = []
    size = 0
    while size < want:
        s = _sentence(rng)
        out.append(s)
        size += len(s) + 1
    return " ".join(out)


def calibrate(backend: Ollama) -> float:
    """Chars per token for this filler under this model's tokenizer, measured rather than
    assumed. A ratio guessed at 4.0 would miss the 27k target by thousands of tokens."""
    rng = random.Random(0)
    block = " ".join(_sentence(rng) for _ in range(400))
    c = backend.complete(block, temperature=0.0, max_tokens=1)
    if c.error or not c.tokens_in:
        sys.exit(f"calibration failed: {c.error}")
    return len(block) / c.tokens_in


def padded_tasks(target_tokens: int, chars_per_token: float):
    """The same N task instances in every cell, with filler prepended. The task text is
    untouched, so the cells are paired instance-for-instance and McNemar applies."""
    for s in range(SEED0, SEED0 + N):
        t = generate("multi_hop", s, depth=DEPTH, distractors=DISTRACTORS)
        if target_tokens > 0:
            rng = random.Random(s * 7919 + target_tokens)
            t.prompt = filler(target_tokens, rng, chars_per_token) + "\n\n" + t.prompt
        t.difficulty = {**t.difficulty, "pad_target": target_tokens}
        yield t


# ------------------------------------------------------------------ run
def run(only: str | None) -> None:
    want = {x.strip() for x in only.split(",")} if only else None
    writer = TraceWriter(EXPERIMENT)
    probe = Ollama(MODEL, num_ctx=4096, timeout=TIMEOUT)
    if not probe.available():
        sys.exit("ollama unavailable (is `ollama serve` running?)")
    cpt = calibrate(probe)
    print(f"calibration: {cpt:.3f} chars/token for this filler under {MODEL}")

    cells = []
    for label, ctx, pad in CELLS:
        if want and label not in want:
            continue
        backend = Ollama(MODEL, num_ctx=ctx, timeout=TIMEOUT)
        cfg = {"experiment": "012", "model": MODEL, "num_ctx": ctx,
               "pad_target": pad, "depth": DEPTH, "distractors": DISTRACTORS,
               "chars_per_token": round(cpt, 4), "max_tokens": MAX_TOK}
        c = run_cell(backend, padded_tasks(pad, cpt), label=label, experiment=EXPERIMENT,
                     config=cfg, temperature=TEMP, max_tokens=MAX_TOK, writer=writer)
        # Truncation guard. ollama drops from the FRONT, and the task sits at the end, so a
        # truncated call still answers -- it just answers with less context than the label
        # claims. That is a silently mislabelled cell, which is worse than a crash.
        avg_in = c.tokens_in / max(c.n, 1)
        if avg_in > ctx - MAX_TOK:
            sys.exit(f"TRUNCATED: {label} averaged {avg_in:.0f} prompt tokens against "
                     f"num_ctx={ctx} less {MAX_TOK} reserved for output")
        cells.append(c)
        print(f"  {label}: mean prompt {avg_in:.0f} tok, num_ctx {ctx}")
    print(table(cells, f"012 -- context length, {MODEL}, multi_hop depth {DEPTH}, n={N}"))


# ------------------------------------------------------------------ report
def _rows():
    by = defaultdict(list)
    for ep in read(ROOT / "results" / f"{EXPERIMENT}.jsonl"):
        cfg = ep.get("config", {})
        if cfg.get("experiment") != "012":
            continue
        st = ep["steps"][0]
        by[cfg["label"]].append({
            "seed": ep["seed"], "ok": bool(ep.get("verdict")),
            "fmt": bool(st.get("meta", {}).get("format_ok")),
            "tin": st.get("tokens_in", 0), "tout": st.get("tokens_out", 0),
            "prefill": st.get("meta", {}).get("prefill_s"),
            "decode": st.get("meta", {}).get("decode_s"),
            "wall": st.get("latency_ms", 0) / 1000,
            "ctx": cfg.get("num_ctx"),
        })
    return by


def report() -> None:
    by = _rows()
    order = [lab for lab, _, _ in CELLS if lab in by]
    if ANCHOR not in by:
        sys.exit("no anchor cell in the trace -- run it first")
    base = {r["seed"]: r["ok"] for r in by[ANCHOR]}

    print(f"\nACCURACY  (n={N}, paired on seeds {SEED0}..{SEED0 + N - 1}, "
          f"McNemar vs {ANCHOR})")
    print(f"{'cell':<18}{'ctx':>7}{'prompt tok':>12}{'acc':>7}  {'95% CI':<14}"
          f"{'fmt':>6}{'p':>9}")
    for lab in order:
        rs = by[lab]
        k, n = sum(r["ok"] for r in rs), len(rs)
        lo, hi = wilson(k, n)
        shared = [r for r in rs if r["seed"] in base]
        _, _, p = mcnemar([base[r["seed"]] for r in shared], [r["ok"] for r in shared])
        fmt = sum(r["fmt"] for r in rs) / max(n, 1)
        tin = statistics.median(r["tin"] for r in rs)
        p_s = "--" if lab == ANCHOR else f"{p:.3f}"
        print(f"{lab:<18}{rs[0]['ctx']:>7}{tin:>12.0f}{k / n:>7.2f}  "
              f"[{lo:.2f},{hi:.2f}]  {fmt:>5.2f}{p_s:>9}")

    print(f"\nSPEED  (median per call)")
    print(f"{'cell':<18}{'prompt tok':>12}{'prefill s':>11}{'tok/s':>8}"
          f"{'decode s':>10}{'out tok/s':>11}{'wall s':>9}")
    ref = None
    for lab in order:
        rs = by[lab]
        pf = statistics.median(r["prefill"] for r in rs if r["prefill"] is not None)
        dc = statistics.median(r["decode"] for r in rs if r["decode"] is not None)
        tin = statistics.median(r["tin"] for r in rs)
        tout = statistics.median(r["tout"] for r in rs)
        wall = statistics.median(r["wall"] for r in rs)
        pre_rate, dec_rate = tin / pf if pf else 0, tout / dc if dc else 0
        if lab == ANCHOR:
            ref = (pre_rate, dec_rate)
        print(f"{lab:<18}{tin:>12.0f}{pf:>11.2f}{pre_rate:>8.0f}"
              f"{dc:>10.2f}{dec_rate:>11.1f}{wall:>9.2f}")
    if ref:
        last = order[-1]
        rs = by[last]
        pf = statistics.median(r["prefill"] for r in rs if r["prefill"] is not None)
        dc = statistics.median(r["decode"] for r in rs if r["decode"] is not None)
        tin = statistics.median(r["tin"] for r in rs)
        tout = statistics.median(r["tout"] for r in rs)
        print(f"\nthroughput at {last} vs {ANCHOR}: "
              f"prefill {tin / pf:.0f} vs {ref[0]:.0f} tok/s "
              f"({(tin / pf) / ref[0] - 1:+.0%}), "
              f"decode {tout / dc:.1f} vs {ref[1]:.1f} tok/s "
              f"({(tout / dc) / ref[1] - 1:+.0%})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--only", default=None,
                   help="comma-separated cell labels; default is all six")
    sub.add_parser("report")
    a = ap.parse_args()
    (run(a.only) if a.cmd == "run" else report())
