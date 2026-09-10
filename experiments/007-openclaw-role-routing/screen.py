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
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.trace import TraceWriter                                  # noqa: E402
from lib.worlds import generate                                    # noqa: E402
from lib.worlds.repair import cell_id                              # noqa: E402

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

# The binding quota is *input tokens per minute*, not requests. Measured on the first
# screen run (2026-09-10): quotaId GenerateContentInputTokensPerModelPerMinute-FreeTier,
# value 250,000, retryDelay ~50s. An agent loop resends the whole conversation every
# turn, so a 10-12 call instance costs ~60,600 input tokens (~5,500/call) and three
# instances inside one minute breach the cap. Pacing on request count does not bound
# this -- that is why the first run lost 3 of 10 instances to 429 aborts.
# Budget on the tokens the *quota* counts, not the billed `input` field. cacheRead is
# ~16,200 of the ~21,000 per call (system prompt + tool schemas) and the quota counts it,
# so one 10-call instance is ~220,000 -- 87% of a minute on its own. Pacing on `input`
# under-counted by 3-4x and cost 7 of 10 instances on the second run.
TPM_CAP = 250_000
TPM_TARGET = 235_000
EXPECTED_PER_INSTANCE = 230_000     # measured 217,628-241,307 over three completed runs
RETRIES = 2                   # a 429 aborts before editing, so a retry starts clean


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


def run_one(m: dict, model: str, template: str, timeout: int,
            lean: bool = False) -> tuple[int, str, str]:
    """One agent turn in the sandbox. Returns (exit code, stdout, stderr).

    The full tool surface is the default, unlike the pilot. `--local-model-lean` existed
    there only to squeeze a turn under Groq's 8k TPM; at Flash Lite's 250K TPM the
    measured 16.7k-token default surface fits with room to spare, and screening arm A on
    a reduced toolset would understate it and bias the result toward a false floor."""
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
        *(["--local-model-lean"] if lean else []),
        "--code-mode", "direct",
        "--cwd", "/work", "--state-dir", "/state",
        "--timeout", str(timeout), "--json",
        "--message-file", "/work/TASK.md",
    ]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 120)
    return p.returncode, p.stdout, p.stderr


def _pace(window: deque, expected: int = EXPECTED_PER_INSTANCE) -> float:
    """Block until `expected` more input tokens fit inside the trailing-60s budget.

    Token-aware, because the cap is token-denominated. Returns seconds waited."""
    waited = 0.0
    while True:
        now = time.time()
        while window and now - window[0][0] > 60:
            window.popleft()
        used = sum(t for _, t in window)
        if used + expected <= TPM_TARGET or not window:
            return waited
        sleep_for = max(1.0, 61 - (now - window[0][0]))
        time.sleep(sleep_for)
        waited += sleep_for


def run(model: str, template: str, budget: int, timeout: int, lean: bool = False) -> None:
    manifest = prepare()
    writer = TraceWriter("007_screen")
    spent = 0
    rows = []
    window: deque = deque()
    print(f"screen: n={len(manifest)}  model={model}  budget={budget} requests")
    print(f"        pacing to {TPM_TARGET:,} quota tok/min against a {TPM_CAP:,} cap\n")

    for i, m in enumerate(manifest, 1):
        if spent >= budget:
            print(f"\nbudget spent ({spent}/{budget}) after {i - 1} instances -- stopping.")
            break

        ws = Path(m["workspace"])
        state = ws.parent / "state"
        for attempt in range(RETRIES + 1):
            if attempt or i > 1:
                waited = _pace(window)
                if waited:
                    print(f"        paced {waited:.0f}s to stay under the token cap")
            t0 = time.time()
            try:
                rc, out, err = run_one(m, model, template, timeout, lean)
            except subprocess.TimeoutExpired:
                rc, out, err = -1, "", "harness timeout"
            wall = time.time() - t0

            toks = oc_export.quota_tokens(state)
            window.append((time.time(), toks))
            spent += oc_export.count_model_calls(state)
            # Authoritative, unlike a stderr grep: the first run's stderr heuristic
            # produced a false positive on an instance that completed fine.
            limited = oc_export.rate_limit_error(state)
            if not limited or attempt == RETRIES:
                break
            # Honour the delay Google supplied. Retrying immediately spends another
            # request on another 429; the pacer's own window cannot see the quota a
            # *rejected* attempt consumed, so its headroom estimate is not trustworthy here.
            delay = oc_export.rate_limit_delay(state) + 5
            print(f"        {m['task_id']}: {limited} -- waiting {delay:.0f}s, "
                  f"retry {attempt + 1}/{RETRIES}")
            time.sleep(delay)
            # A 429 aborts before the agent edits anything, so the workspace is still a
            # clean starting state; rebuild it anyway rather than assume that.
            shutil.rmtree(ws); shutil.rmtree(state, ignore_errors=True)
            generate(m["seed"]).materialize(ws)
            state.mkdir(exist_ok=True)

        w = generate(m["seed"])
        v = w.check(ws)
        ep = oc_export.export(state, m["task_id"], m["seed"], arm="A",
                              config={"model": model, "rc": rc, "lean": lean,
                                      "wall_s": round(wall, 1)})
        ep.finish(verdict=bool(v.passed))
        # `edited` is the tool-using analogue of 001's format_ok column: an agent that
        # never wrote anything and one that wrote a wrong fix are different failures.
        ep.config["edited"] = bool(v.edited)
        ep.config["rate_limited"] = limited
        writer.write(ep)

        rows.append({"task_id": m["task_id"], "seed": m["seed"],
                     "passed": bool(v.passed),
                     "edited": bool(v.edited), "calls": ep.config["api_requests"],
                     "quota_tokens": toks, "rc": rc, "wall_s": round(wall, 1),
                     "rate_limited": limited})
        flag = "PASS" if v.passed else ("edited, still failing" if v.edited else "untouched")
        print(f"  {i:2d}/{len(manifest)}  {m['task_id']:26s} {flag:22s} "
              f"{ep.config['api_requests']:3d} calls {toks:7,d} qtok {wall:5.0f}s "
              f"[{spent}/{budget}]" + ("  RATE-LIMITED" if limited else ""))

    (RUNS / "screen.json").write_text(json.dumps(rows, indent=2))
    print(f"\n  traces -> {writer.path}")
    _verdict(rows, spent)


def _verdict(rows: list[dict], spent: int = 0) -> None:
    """Report the clean-run rate, not the raw rate.

    A 429 abort is a harness event, not a capability failure: the agent never got to
    work. The first screen run (2026-09-10) scored 7/10 = 0.70 and read FUNDABLE, but all
    three failures were 429s and every instance that ran to completion passed -- 7/7,
    which is a CEILING. Counting the two kinds of failure together inverted the verdict."""
    if not rows:
        print("  no instances completed.")
        return
    n = len(rows)
    raw = sum(r["passed"] for r in rows)
    clean = [r for r in rows if not r["rate_limited"]]
    limited = n - len(clean)
    print(f"\n  raw          {raw}/{n} = {raw / n:.2f}   (counts 429 aborts as failures)")
    if not clean:
        print("  every instance was rate-limited: no capability signal at all.")
        return
    cp = sum(r["passed"] for r in clean)
    p = cp / len(clean)
    lo, hi = _wilson(cp, len(clean))
    print(f"  clean        {cp}/{len(clean)} = {p:.2f}   Wilson95 [{lo:.2f}, {hi:.2f}]")
    print(f"  rate-limited {limited}/{n}   edited {sum(r['edited'] for r in rows)}/{n}"
          f"   {spent} requests")
    tried_and_failed = sum(1 for r in clean if not r["passed"] and r["edited"])
    print(f"  worked the task and got it wrong: {tried_and_failed}")
    if p < 0.25:
        print("  -> FLOOR (<0.25). Backend cannot fund 007; a floored arm is not a comparison.")
    elif p > 0.85:
        print("  -> CEILING (>0.85). Harden the 12-defect pool before running three arms.")
    else:
        print("  -> FUNDABLE (0.25-0.85). Pick k and n from the RPD budget.")
    cells = len({cell_id(generate(r["seed"])) for r in clean if "seed" in r}) or len(clean)
    print(f"  n={len(clean)} clean, {cells} distinct pool cells. Says nothing about repair "
          "tasks in general.")


def _wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    from math import sqrt
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def report() -> None:
    path = RUNS / "screen.json"
    if not path.exists():
        sys.exit(f"no screen at {path} -- run it first")
    rows = json.loads(path.read_text())
    for r in rows:
        flag = "PASS" if r["passed"] else ("edited" if r["edited"] else "untouched")
        print(f"  {r['task_id']:26s} {flag:12s} {r['calls']:3d} calls  {r['wall_s']:5.0f}s"
              + (f"  [{r['rate_limited']}]" if r.get("rate_limited") else ""))
    _verdict(rows, sum(r["calls"] for r in rows))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--model", default="gemini/gemini-3.5-flash-lite")
    r.add_argument("--template", default="gemini.template.json")
    r.add_argument("--budget", type=int, default=DEFAULT_BUDGET)
    r.add_argument("--timeout", type=int, default=360)
    r.add_argument("--lean", action="store_true",
                   help="reduced tool surface; only needed on a TPM-starved backend")
    sub.add_parser("report")
    a = p.parse_args()
    if a.cmd == "run":
        run(a.model, a.template, a.budget, a.timeout, a.lean)
    else:
        report()


if __name__ == "__main__":
    main()
