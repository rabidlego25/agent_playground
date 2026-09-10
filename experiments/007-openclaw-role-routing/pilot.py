"""007 pilot -- harness check, not a finding.

Its whole job is to replace the guesses in sandbox/README.md with observed facts, on
n=10 instances. Nothing it produces is an experimental result: the arms are not matched,
the instance pool is 12 defects wide, and the point is to learn what the runtime does.

What it must pin down:
  - the non-interactive invocation for one task in one workspace
  - the session SQLite path and schema, so the trace exporter targets real tables
  - whether --model-map holds one model across all nine agents
  - what an agentToAgent message looks like in the log (H3 is not computable without it)
  - per-call HTTP status and retry counts, because a rate-limited free tier that drops
    calls would make arm B look worse for reasons that are not deliberation

Usage:  uv run experiments/007-openclaw-role-routing/pilot.py prepare|score
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.worlds import generate                                   # noqa: E402

HERE = Path(__file__).parent
PILOT = HERE / "runs" / "pilot"
N = 10
SEEDS = range(700, 700 + N)


def prepare() -> None:
    """Materialize one workspace per instance. Idempotent: rebuilds from scratch, because
    a workspace an agent has already touched is not a starting state."""
    if PILOT.exists():
        shutil.rmtree(PILOT)
    PILOT.mkdir(parents=True)
    manifest = []
    for seed in SEEDS:
        w = generate(seed)
        ws = w.materialize(PILOT / w.task_id / "ws")
        pre = w.check(ws)
        assert not pre.passed, f"{w.task_id}: ships already passing"
        manifest.append({
            "task_id": w.task_id, "seed": seed, "module": w.module_name,
            "workspace": str(ws.relative_to(PILOT)),
            "difficulty": w.difficulty,
            "shipped_verdict": pre.as_dict(),
        })
    (PILOT / "manifest.jsonl").write_text(
        "".join(json.dumps(m) + "\n" for m in manifest))
    print(f"prepared {len(manifest)} workspaces under {PILOT}")
    for m in manifest:
        d = m["difficulty"]
        print(f"  {m['task_id']:26s} {d['template']}/m{d['mutation']}  "
              f"shipped {m['shipped_verdict']['cases_passed']}/"
              f"{m['shipped_verdict']['cases_total']}")


def score() -> None:
    """Re-score every workspace after an arm has run in it."""
    rows = [json.loads(l) for l in (PILOT / "manifest.jsonl").read_text().splitlines()]
    passed = edited = 0
    for m in rows:
        w = generate(m["seed"])
        v = w.check(PILOT / m["workspace"])
        passed += v.passed
        edited += v.edited
        flag = "PASS" if v.passed else ("edited, still failing" if v.edited else "untouched")
        print(f"  {m['task_id']:26s} {v.cases_passed}/{v.cases_total}  {flag}"
              + (f"  [{v.error}]" if v.error else ""))
    print(f"\n  repaired {passed}/{len(rows)}   edited {edited}/{len(rows)}")
    print("  'untouched' is the tool-using analogue of a format failure: an agent that never"
          "\n  wrote anything and one that wrote a wrong fix are different failures.")


if __name__ == "__main__":
    {"prepare": prepare, "score": score}[sys.argv[1] if len(sys.argv) > 1 else "prepare"]()
