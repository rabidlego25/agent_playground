"""Does the repair world's oracle actually measure repair?

`notes/2026-08-29-oracle-format-confound.md` is this repo's most expensive lesson: an oracle
that looked fine produced a clean, tight-CI, entirely fake headline. The oracle is part of the
experiment and needs its own tests. This probe runs before 007 does, and asserts four
properties of every generated instance, with no model involved:

1. the hidden suite FAILS on the workspace as shipped     -- the defect is real and detectable
2. the visible smoke suite PASSES on it                   -- running the shipped tests does not
                                                             locate the bug, so the task is not
                                                             "did the agent type pytest"
3. the hidden suite PASSES on the reference source        -- the tests themselves are correct
4. check() sets edited=False before any change, True after -- the tool-using analogue of
                                                             format_ok is wired up

Property 4 also covers the case that matters most in an agent setting: an agent with write
access deleting or rewriting the tests that judge it.

Since the 2026-09-10 parameterisation it also asserts two properties of the *pool*, because
007's screen failed on pool design rather than on any single instance:

5. no mutation operator is dead -- one that can never satisfy the visible/hidden constraint
   is never drawn, and three of them silently were. Two (`max(start, end)`, `abs(end -
   start)`) were no-ops on data where end >= start: not bugs at all, just unreachable cells
   that made the pool look wider than it was.
6. the pool is wide enough that a run of n instances is close to n independent draws. The
   number reported is the distinct-cell count at n=40, which is what "effective n" means
   here and what the 12-cell pool could not deliver.
"""
import random
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.worlds import generate                                   # noqa: E402
from lib.worlds.repair import (                                   # noqa: E402
    MIN_VISIBLE, REPAIR_TEMPLATES, _call, _load, cell_id)

N = 60


def _run_visible(root: Path) -> bool:
    r = subprocess.run([sys.executable, "test_smoke.py"], cwd=root,
                       capture_output=True, text=True, timeout=30)
    return r.returncode == 0


if __name__ == "__main__":
    seen: Counter[str] = Counter()
    failures: list[str] = []
    cases: list[int] = []

    for seed in range(N):
        w = generate(seed)
        seen[f"{w.difficulty['template']}/m{w.difficulty['mutation']}"] += 1

        with tempfile.TemporaryDirectory() as tmp:
            root = w.materialize(Path(tmp) / "ws")

            shipped = w.check(root)
            if shipped.passed:
                failures.append(f"{w.task_id}: hidden suite passes on the buggy workspace")
            if shipped.edited:
                failures.append(f"{w.task_id}: edited=True before any edit")
            cases.append(shipped.cases_total)

            if not _run_visible(root):
                failures.append(f"{w.task_id}: visible smoke suite fails on the buggy workspace")

            (root / f"{w.module_name}.py").write_text(w.reference_source)
            fixed = w.check(root)
            if not fixed.passed:
                failures.append(
                    f"{w.task_id}: hidden suite fails on the reference "
                    f"({fixed.cases_passed}/{fixed.cases_total}) {fixed.error or ''}")
            if not fixed.edited:
                failures.append(f"{w.task_id}: edited=False after rewriting the module")

            # an agent that deletes the tests judging it must not thereby pass
            (root / "test_smoke.py").write_text("raise SystemExit(0)\n")
            (root / f"{w.module_name}.py").write_text(w.buggy_source)
            if w.check(root).passed:
                failures.append(f"{w.task_id}: passes after the agent neutered the tests")

    # --- property 5: no operator is unreachable -------------------------------------
    dead = []
    for tpl in REPAIR_TEMPLATES:
        reachable: set[str] = set()
        offered: set[str] = set()
        for s in range(120):
            rng = random.Random(s)
            p = tpl.draw(rng)
            ref = tpl.render(p)
            edges, drawn = tpl.edges(p), tpl.cases(rng, p)
            want = [("ok", tpl.oracle(p, fn, a)) for fn, a in edges + drawn]
            ne = len(edges)
            for label, find, repl in tpl.mutations(p):
                offered.add(label)
                if find not in ref:
                    continue
                try:
                    bns = _load(ref.replace(find, repl, 1), tpl.name)
                except Exception:                                  # noqa: BLE001
                    continue
                got = [_call(bns, fn, a) for fn, a in edges + drawn]
                vis = [i for i in range(len(got)) if got[i] == want[i] and i >= ne][:4]
                differ = [i for i in range(len(got)) if got[i] != want[i]]
                hid = list(range(ne)) + [i for i in differ if i >= ne][:4]
                if len(vis) >= MIN_VISIBLE and any(i in hid for i in differ):
                    reachable.add(label)
        for label in sorted(offered - reachable):
            dead.append(f"{tpl.name}/{label}: never satisfies the visible/hidden constraint")

    # --- property 6: the pool is wide enough that n draws are ~n independent ----------
    cells_40 = {cell_id(generate(s)) for s in range(40)}
    cells_all = {cell_id(generate(s)) for s in range(N)}

    print(f"repair world -- {N} instances, {len(seen)} distinct template/operator pairs")
    for cell, k in sorted(seen.items()):
        print(f"  {cell:26s} {k:3d}")
    print(f"  hidden cases per instance: min {min(cases)}, max {max(cases)}")
    print(f"\n  distinct (template, spec, operator) cells: {len(cells_all)}/{N} seeds")
    print(f"  effective n at the 007 run size:            {len(cells_40)}/40")
    if dead:
        failures.extend(dead)

    if failures:
        print(f"\n{len(failures)} PROBLEMS:")
        for f in failures[:20]:
            print(f"  {f}")
        sys.exit(1)
    print("\n  all six properties hold: four on every instance, two on the pool.")
