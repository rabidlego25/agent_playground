"""007 capability screen -- arm A only, is the backend off the floor?

Not a comparison and not a finding. 007's own rule, learned expensively in 003, is that a
floored arm is not a comparison, so this measures one thing: does a single well-prompted
agent on the chosen backend repair anything at all in `lib/worlds/repair.py`.

**Decision rule, committed 2026-09-10 before the first run:**

  pass rate < 0.25   the backend floors; free tier is dead for 007 whatever its RPD
  pass rate > 0.85   the 12 defects cannot separate three arms; harden the pool first
  otherwise          the design is fundable; pick k and n from the RPD budget

n=10 on a 12-defect pool. This bounds nothing about repair tasks in general and is not
written up as though it does.

Budget guard: Google AI Studio's free tier is metered in *requests per day*, not tokens,
so the cap here counts model calls (via export.count_model_calls) after every instance
and stops the sweep when the budget is spent. Overrunning costs nothing but tomorrow's
quota -- the project is unbilled, so there is no overage path -- but a sweep that
silently eats the day's budget wastes a day.

Usage:
    uv run experiments/007-openclaw-role-routing/screen.py run --model gemini/gemini-3.5-flash-lite
    uv run experiments/007-openclaw-role-routing/screen.py report
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.trace import TraceWriter                                  # noqa: E402
from lib.worlds import generate                                    # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
import export as oc_export                                         # noqa: E402

HERE = Path(__file__).parent
SANDBOX = HERE / "sandbox"
RUNS = HERE / "runs" / "screen"
N = 10
SEEDS = range(700, 700 + N)
IMAGE = "openclaw-007"
ENV_FILE = Path.home() / "Documents/scratch/keys/openclaw.env"

# 500 RPD on Gemini 3.5 Flash Lite. 400 leaves room to re-run a failed instance and to
# inspect a session without the screen having eaten the whole day.
DEFAULT_BUDGET = 400
# 15 RPM. Turn-level pacing cannot govern the calls *inside* one agent turn, so this is a
# floor on the gap between turns, not a guarantee -- 429s inside a turn are recorded
# rather than prevented, and their rate is one of the things the screen is measuring.
MIN_TURN_GAP_S = 8.0


def prepare() -> list[dict]:
    """Fresh workspaces. A workspace an agent has already touched is not a starting
    state, so this always rebuilds."""
    if RUNS.exists():
        shutil.rmtree(RUNS)
    RUNS.mkdir(parents=True)
    manifest = []
    for seed in SEEDS:
        w = generate(seed)
        ws = w.materialize(RUNS / w.task_id / "ws")
        pre = w.check(ws)
        assert not pre.passed, f"{w.task_id}: ships already passing"
        manifest.append({"task_id": w.task_id, "seed": seed,
                         "workspace": str(ws), "module": w.module_name})
    (RUNS / "manifest.jsonl").write_text(
        "".join(json.dumps(m) + "\n" for m in manifest))
    return manifest


def run_one(m: dict, model: str, template: str, timeout: int) -> tuple[int, str, str]:
    """One agent turn in the sandbox. Returns (exit code, stdout, stderr)."""
    ws = Path(m["workspace"])
    state = ws.parent / "state"
    state.mkdir(exist_ok=True)
    cmd = [
        "docker", "run", "--rm",
        "--env-file", str(ENV_FILE),
        "-v", f"{SANDBOX / 'config' / template}:/cfg/openclaw.template.json:ro",
        "-v", f"{SANDBOX / 'entrypoint.sh'}:/entrypoint.sh:ro",
        "-v", f"{ws}:/work",
        "-v", f"{state}:/state",
        IMAGE, "bash", "/entrypoint.sh",
        "--model", model,
        "--local-model-lean", "--code-mode", "direct",
        "--cwd", "/work", "--state-dir", "/state",
        "--timeout", str(timeout), "--json",
        "--message-file", "/work/TASK.md",
    ]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 120)
    return p.returncode, p.stdout, p.stderr


def run(model: str, template: str, budget: int, timeout: int) -> None:
    manifest = prepare()
    writer = TraceWriter("007_screen")
    spent = 0
    rows = []
    print(f"screen: n={len(manifest)}  model={model}  budget={budget} requests\n")

    for i, m in enumerate(manifest, 1):
        if spent >= budget:
            print(f"\nbudget spent ({spent}/{budget}) after {i - 1} instances -- stopping.")
            break
        if i > 1:
            time.sleep(MIN_TURN_GAP_S)

        t0 = time.time()
        try:
            rc, out, err = run_one(m, model, template, timeout)
        except subprocess.TimeoutExpired:
            rc, out, err = -1, "", "harness timeout"
        wall = time.time() - t0

        state = Path(m["workspace"]).parent / "state"
        calls = oc_export.count_model_calls(state)
        spent += calls

        w = generate(m["seed"])
        v = w.check(Path(m["workspace"]))

        ep = oc_export.export(state, m["task_id"], m["seed"], arm="A",
                              config={"model": model, "rc": rc, "wall_s": round(wall, 1)})
        ep.finish(verdict=bool(v.passed))
        # `edited` is the tool-using analogue of 001's format_ok column: an agent that
        # never wrote anything and one that wrote a wrong fix are different failures.
        ep.config["edited"] = bool(v.edited)
        ep.config["rate_limited"] = ("429" in err) or ("rate" in err.lower() and "limit" in err.lower())
        writer.write(ep)

        rows.append({"task_id": m["task_id"], "passed": bool(v.passed),
                     "edited": bool(v.edited), "calls": calls,
                     "rc": rc, "wall_s": round(wall, 1),
                     "rate_limited": ep.config["rate_limited"]})
        flag = "PASS" if v.passed else ("edited, still failing" if v.edited else "untouched")
        print(f"  {i:2d}/{len(manifest)}  {m['task_id']:26s} {flag:22s} "
              f"{calls:3d} calls  {wall:5.0f}s  [{spent}/{budget}]")

    (RUNS / "screen.json").write_text(json.dumps(rows, indent=2))
    print(f"\n  traces -> {writer.path}")
    _verdict(rows, spent)
    if rows:
        print("\n  Run `export.py describe` on one state dir before trusting these traces:\n"
              f"    uv run {Path(__file__).parent}/export.py describe "
              f"{Path(manifest[0]['workspace']).parent / 'state'}")


def _verdict(rows: list[dict], spent: int = 0) -> None:
    if not rows:
        print("  no instances completed.")
        return
    n = len(rows)
    p = sum(r["passed"] for r in rows) / n
    edited = sum(r["edited"] for r in rows)
    limited = sum(r["rate_limited"] for r in rows)
    print(f"\n  pass {sum(r['passed'] for r in rows)}/{n} = {p:.2f}   "
          f"edited {edited}/{n}   rate-limited {limited}/{n}   {spent} requests")
    if p < 0.25:
        print("  -> FLOOR (<0.25). Backend cannot fund 007; a floored arm is not a comparison.")
    elif p > 0.85:
        print("  -> CEILING (>0.85). Harden the 12-defect pool before running three arms.")
    else:
        print("  -> FUNDABLE (0.25-0.85). Pick k and n from the RPD budget.")
    print(f"  n={n} on a 12-defect pool. Says nothing about repair tasks in general.")


def report() -> None:
    path = RUNS / "screen.json"
    if not path.exists():
        sys.exit(f"no screen at {path} -- run it first")
    rows = json.loads(path.read_text())
    for r in rows:
        flag = "PASS" if r["passed"] else ("edited" if r["edited"] else "untouched")
        print(f"  {r['task_id']:26s} {flag:12s} {r['calls']:3d} calls  {r['wall_s']:5.0f}s")
    _verdict(rows, sum(r["calls"] for r in rows))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--model", default="gemini/gemini-3.5-flash-lite")
    r.add_argument("--template", default="gemini.template.json")
    r.add_argument("--budget", type=int, default=DEFAULT_BUDGET)
    r.add_argument("--timeout", type=int, default=360)
    sub.add_parser("report")
    a = p.parse_args()
    if a.cmd == "run":
        run(a.model, a.template, a.budget, a.timeout)
    else:
        report()


if __name__ == "__main__":
    main()
