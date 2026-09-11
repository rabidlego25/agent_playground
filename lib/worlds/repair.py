"""Bug-repair workspaces: a small package with one injected defect and hidden tests.

Built for 007, which compares agent configurations that use tools. Those need a task with
three properties that `lib.tasks` families do not have:

1. **A workspace, not a prompt.** The agent reads and edits files and runs commands.
2. **A binary oracle that no judge is involved in.** 002 exists because the suspicion is
   that LLM judges reward confident packaging; do not put one in the scoring path.
3. **Visible tests that pass on the broken code.** If running the shipped test suite
   located the bug, the task would measure "did the agent run pytest" and nothing else.
   The visible smoke tests here pass *before* the fix; only the hidden suite catches the
   defect. That is also what makes the task discriminating between configurations —
   the work is in reading the specification and the code, not in reading a red test.

**The hidden tests never touch the workspace.** An agent with write access can edit any
file it can see, including a test that judges it. `check()` copies the workspace to a
temporary directory, writes the hidden suite there, and runs it out of the agent's reach.

## Parameterisation (2026-09-10)

The first version had 3 templates x 4 mutation operators = **12 fixed cells**, with the
specification, the constants and every test case hardcoded. 007's screen then measured arm
A at 7/7 on ten draws from that pool, which is the pre-registered ceiling condition: a pool
that one agent solves every time cannot separate three arms. `experiments/007-.../SCREEN.md`
has the numbers.

What varies per seed now:

- **The specification itself.** Whether touching intervals merge, whether a fee may breach
  the overdraft limit, whether the grid is 4- or 8-connected, what the overdraft floor is,
  which character is a wall. The statement is rendered from those draws, so the *correct
  fix differs between seeds* rather than the same fix being reachable from memory.
- **The constants and shapes** — coordinate scales, balances, grid dimensions, wall density.
- **The test inputs**, drawn per seed rather than listed.
- **The mutation operator**, from a wider set per template.

Expected values are computed by an **independent implementation of the specification**
(`_oracle` per template, deliberately a different algorithm from the one under repair —
pairwise-union against sort-sweep, Bellman-Ford relaxation against BFS). They are not read
off the reference module. Generation asserts the reference agrees with that oracle on every
case, so `probe_repair_world.py` property 3 stays a real check rather than a tautology.

Visible and hidden cases are then *selected* by execution, per seed:

- visible = drawn cases where the mutant still agrees with the oracle (the bug is invisible)
- hidden  = spec-corner cases plus drawn cases, requiring at least one where the mutant
            disagrees (the bug is detectable)

A mutation that cannot satisfy both is rejected and another is drawn, so properties 1 and 2
of the probe hold by construction on every instance rather than by hand-checking.
"""

from __future__ import annotations

import copy
import os
import random
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

__all__ = ["generate", "RepairWorld", "Verdict", "REPAIR_TEMPLATES", "cell_id"]

# A drawn case set has to leave the bug invisible to the smoke suite and visible to the
# hidden suite. These are the minimums; generation redraws the operator if one fails.
MIN_VISIBLE = 2
MIN_DISCRIMINATING = 1
N_CANDIDATES = 26

# Fraction of seeds that prefer a defect spanning several edits.
#
# Raised to 0.6 on 2026-09-11 to harden the pool, then cut to 0.2 the same day when the
# measurement came back the other way round: multi-edit defects are *easier*, 9/9 against
# 6/11 for single-edit, Fisher one-sided p=0.0298 at n=20. A defect spanning two edits
# breaks more behaviour in more places, so the agent's own probe tests find it on the first
# try, while a quiet one-line error survives that probing. Difficulty is set by
# detectability under the agent's own testing, not by the size of the fix. See
# notes/2026-09-11-defect-detectability-not-edit-count.md.
#
# 0.2 mixes the sub-pools to a predicted 0.2*1.00 + 0.8*0.55 = 0.64, inside the 0.60-0.70
# band 007 needs. That prediction comes from the same n=20 that produced the finding and
# is unvalidated on held-out seeds.
MULTI_EDIT_RATE = 0.2


@dataclass
class Verdict:
    """Outcome of scoring a workspace. `edited` is the tool-using analogue of format_ok:
    an agent that never wrote anything and one that wrote a wrong fix are different
    failures, and 001's oracle bug is what happens when you collapse that distinction."""

    passed: bool
    cases_passed: int
    cases_total: int
    edited: bool
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "cases_passed": self.cases_passed,
            "cases_total": self.cases_total,
            "edited": self.edited,
            "error": self.error,
        }


@dataclass
class RepairWorld:
    task_id: str
    family: str
    seed: int
    statement: str                    # what the agent is told
    module_name: str
    buggy_source: str                 # what lands in the workspace
    reference_source: str             # never written to the workspace
    visible_tests: str                # passes on buggy_source, by construction
    hidden_tests: str                 # applied only in check(), in a copy
    hidden_cases: int = 0
    difficulty: dict[str, Any] = field(default_factory=dict)

    def materialize(self, root: str | Path) -> Path:
        """Write the starting workspace. Returns the directory."""
        root = Path(root)
        root.mkdir(parents=True, exist_ok=True)
        (root / f"{self.module_name}.py").write_text(self.buggy_source)
        (root / "test_smoke.py").write_text(self.visible_tests)
        (root / "TASK.md").write_text(self.statement)
        return root

    def check(self, root: str | Path, timeout: int = 30) -> Verdict:
        """Score the workspace. Nothing inside `root` is trusted: the hidden suite is
        written into a copy, so an agent that edited or deleted a test cannot affect it."""
        root = Path(root)
        src = root / f"{self.module_name}.py"
        if not src.exists():
            return Verdict(False, 0, self._case_count(), False, "module missing")
        edited = src.read_text() != self.buggy_source

        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "work"
            # __pycache__ must not travel: a stale .pyc whose source changed by the same
            # byte count within the same second is still considered valid, and the copy
            # then scores the module the agent replaced. Silent, and exactly the class of
            # oracle bug notes/2026-08-29-oracle-format-confound.md is about.
            shutil.copytree(root, work, ignore=shutil.ignore_patterns("__pycache__"))
            for stray in work.glob("test_*.py"):     # the agent's own tests do not score it
                stray.unlink()
            (work / "_hidden.py").write_text(self.hidden_tests)
            try:
                r = subprocess.run(
                    [sys.executable, "-B", "_hidden.py"], cwd=work,
                    capture_output=True, text=True, timeout=timeout,
                    env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
            except subprocess.TimeoutExpired:
                return Verdict(False, 0, self._case_count(), edited, "timeout")
            except OSError as exc:
                return Verdict(False, 0, self._case_count(), edited, str(exc))

        tail = (r.stdout + r.stderr).strip().splitlines()
        summary = next((ln for ln in reversed(tail) if ln.startswith("CASES ")), "")
        try:
            _, got, total = summary.split()
            passed_n, total_n = int(got), int(total)
        except ValueError:
            return Verdict(False, 0, self._case_count(), edited,
                           (tail[-1] if tail else "no output")[:200])
        return Verdict(r.returncode == 0 and passed_n == total_n,
                       passed_n, total_n, edited, None)

    def _case_count(self) -> int:
        return self.hidden_cases


# --------------------------------------------------------------------------------------
# Execution helpers. Cases are selected by running the code, not by hand-reasoning about
# which mutation shows up where -- that reasoning is what silently broke the first pool.
# --------------------------------------------------------------------------------------

def _load(source: str, module_name: str) -> dict[str, Any]:
    ns: dict[str, Any] = {"__name__": module_name}
    exec(compile(source, f"{module_name}.py", "exec"), ns)      # noqa: S102
    return ns


def _call(ns: dict[str, Any], fn: str, args: tuple) -> tuple[str, Any]:
    """Result of one call, with exceptions as values so a mutant that raises is a
    distinguishable outcome rather than a crash during generation."""
    try:
        return ("ok", ns[fn](*copy.deepcopy(args)))
    except Exception as exc:                                     # noqa: BLE001
        return ("err", type(exc).__name__)


def _render_case(fn: str, args: tuple) -> str:
    return f"{fn}({', '.join(repr(a) for a in args)})"


# --------------------------------------------------------------------------------------
# Templates. Each draws its own specification, renders a correct module against it, and
# supplies an independent oracle for that specification.
# --------------------------------------------------------------------------------------

@dataclass
class _Template:
    name: str
    entries: tuple[str, ...]
    draw: Callable[[random.Random], dict]
    render: Callable[[dict], str]
    statement: Callable[[dict], str]
    mutations: Callable[[dict], list[tuple[str, list]]]   # (label, [(find, replace)..])
    oracle: Callable[[dict, str, tuple], Any]
    edges: Callable[[dict], list[tuple[str, tuple]]]
    cases: Callable[[random.Random, dict], list[tuple[str, tuple]]]


# ---------------------------------------- intervals ------------------------------------

def _intervals_draw(rng: random.Random) -> dict:
    return {
        "touching": rng.choice([True, False]),
        "scale": rng.choice([1, 2, 5, 10]),
        "hi": rng.choice([12, 20, 30]),
    }


def _intervals_render(p: dict) -> str:
    op = "<=" if p["touching"] else "<"
    return f'''"""Merge overlapping closed intervals."""


def merge(spans):
    if not spans:
        return []
    ordered = sorted(spans, key=lambda s: s[0])
    out = [list(ordered[0])]
    for start, end in ordered[1:]:
        if start {op} out[-1][1]:
            out[-1][1] = max(out[-1][1], end)
        else:
            out.append([start, end])
    return [tuple(s) for s in out]


def covered(spans):
    return sum(end - start for start, end in merge(spans))
'''


def _intervals_statement(p: dict) -> str:
    touch = ("with touching intervals (`(1, 3)` and `(3, 5)`) counted as overlapping and "
             "combined into `(1, 5)`"
             if p["touching"] else
             "with touching intervals (`(1, 3)` and `(3, 5)`) counted as **separate** — "
             "they must overlap by a non-zero amount to be combined")
    return f"""# Task

`intervals.py` merges overlapping closed intervals and reports total coverage.

`merge(spans)` takes a list of `(start, end)` pairs and returns them merged and sorted,
{touch}.
`covered(spans)` returns the total length covered, counting overlap once.

Something in here is wrong. The smoke tests pass and the module is still incorrect.
Fix `intervals.py` so it matches the specification above. Do not change the function
signatures.
"""


def _intervals_mutations(p: dict) -> list[tuple[str, list]]:
    op = "<=" if p["touching"] else "<"
    flipped = "<" if p["touching"] else "<="
    BOUNDARY = (f"if start {op} out[-1][1]:", f"if start {flipped} out[-1][1]:")
    NO_MAX = ("out[-1][1] = max(out[-1][1], end)", "out[-1][1] = end")
    UNSORTED = ("ordered = sorted(spans, key=lambda s: s[0])", "ordered = list(spans)")
    COVERED_RAW = ("return sum(end - start for start, end in merge(spans))",
                   "return sum(end - start for start, end in spans)")
    return [
        ("boundary", [BOUNDARY]),
        ("no-max", [NO_MAX]),
        ("unsorted", [UNSORTED]),
        ("covered-raw", [COVERED_RAW]),
        # Multi-edit: each edit alone leaves the module still failing, so a fix that
        # changes one line and stops does not pass. Generation verifies that.
        ("boundary+no-max", [BOUNDARY, NO_MAX]),
        ("unsorted+covered", [UNSORTED, COVERED_RAW]),
        ("sort-by-end", [("ordered = sorted(spans, key=lambda s: s[0])",
                          "ordered = sorted(spans, key=lambda s: s[1])")]),
        # Replaced three operators that measured nothing (2026-09-10): `max(start, end)`
        # and `abs(end - start)` are no-ops when end >= start, which it always is here --
        # they were not bugs; and dropping the last span broke every case, so no smoke
        # test could survive. Viability is checked in probe_repair_world.py now.
        ("merge-short", [("out[-1][1] = max(out[-1][1], end)",
                          "out[-1][1] = max(out[-1][1], end) - 1")]),
        ("covered-fencepost", [("return sum(end - start for start, end in merge(spans))",
                                "return sum(end - start + 1 for start, end in merge(spans))")]),
        ("sort-reverse", [("ordered = sorted(spans, key=lambda s: s[0])",
                           "ordered = sorted(spans, key=lambda s: s[0], reverse=True)")]),
    ]


def _intervals_naive(spans: list, touching: bool) -> list[tuple]:
    """Pairwise union to a fixpoint -- a different algorithm from the sort-sweep under
    repair, so agreement between them is evidence rather than restatement."""
    items = [list(s) for s in spans]
    changed = True
    while changed:
        changed = False
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                a, b = items[i], items[j]
                hit = (a[0] <= b[1] and b[0] <= a[1]) if touching else \
                      (a[0] < b[1] and b[0] < a[1])
                if hit:
                    items[i] = [min(a[0], b[0]), max(a[1], b[1])]
                    items.pop(j)
                    changed = True
                    break
            if changed:
                break
    return sorted((tuple(x) for x in items), key=lambda s: s[0])


def _intervals_oracle(p: dict, fn: str, args: tuple) -> Any:
    merged = _intervals_naive(list(args[0]), p["touching"])
    return merged if fn == "merge" else sum(e - s for s, e in merged)


def _intervals_edges(p: dict) -> list[tuple[str, tuple]]:
    s = p["scale"]
    return [
        ("merge", ([],)),
        ("merge", ([(1 * s, 3 * s), (3 * s, 5 * s)],)),          # the touching corner
        ("merge", ([(1 * s, 10 * s), (2 * s, 3 * s)],)),         # containment
        ("merge", ([(5 * s, 6 * s), (1 * s, 2 * s)],)),          # unsorted input
        ("merge", ([(1 * s, 3 * s), (2 * s, 6 * s), (8 * s, 10 * s)],)),
        ("covered", ([(1 * s, 3 * s), (2 * s, 6 * s)],)),
        ("covered", ([(1 * s, 3 * s), (3 * s, 5 * s)],)),
        ("covered", ([(0, 4 * s), (1 * s, 2 * s), (6 * s, 7 * s)],)),
    ]


def _intervals_cases(rng: random.Random, p: dict) -> list[tuple[str, tuple]]:
    out = []
    for _ in range(N_CANDIDATES):
        n = rng.randint(1, 5)
        spans = []
        for _ in range(n):
            a = rng.randrange(0, p["hi"]) * p["scale"]
            b = a + rng.randrange(1, 6) * p["scale"]
            spans.append((a, b))
        out.append((rng.choice(["merge", "covered"]), (spans,)))
    return out


# ---------------------------------------- ledger ---------------------------------------

def _ledger_draw(rng: random.Random) -> dict:
    return {
        "limit": rng.choice([0, 0, -500, -2000]),      # overdraft floor, in cents
        "fee_bypasses": rng.choice([True, False]),
        "unit": rng.choice([1, 25, 100]),
    }


def _ledger_render(p: dict) -> str:
    if p["fee_bypasses"]:
        fee_branch = '''        elif kind == "fee":
            balance -= amount'''
    else:
        fee_branch = f'''        elif kind == "fee":
            if balance - amount < {p["limit"]}:
                rejected += 1
                continue
            balance -= amount'''
    return f'''"""Apply transactions to an opening balance, in whole cents."""

FLOOR = {p["limit"]}


def apply(opening, txns):
    balance = opening
    rejected = 0
    for kind, amount in txns:
        if kind == "credit":
            balance += amount
        elif kind == "debit":
            if balance - amount < FLOOR:
                rejected += 1
                continue
            balance -= amount
{fee_branch}
        else:
            raise ValueError(kind)
    return balance, rejected
'''


def _ledger_statement(p: dict) -> str:
    floor = ("below zero" if p["limit"] == 0
             else f"below the overdraft floor of {p['limit']} cents")
    fee = ("A fee is **always** applied, even if that takes the balance past the floor."
           if p["fee_bypasses"] else
           "A fee that would take the balance past the floor is rejected and skipped too, "
           "and counts toward `rejected`.")
    return f"""# Task

`ledger.py` applies a list of transactions to an opening balance.

`apply(opening, txns)` processes each `(kind, amount)` in order. `kind` is `"credit"`,
`"debit"` or `"fee"`. A debit that would take the balance {floor} is rejected and
skipped entirely. {fee} `apply` returns `(balance, rejected)` where `rejected` is the
count of skipped transactions. All amounts are in whole cents; the balance is an int
throughout.

Something in here is wrong. The smoke tests pass and the module is still incorrect.
Fix `ledger.py` so it matches the specification above. Do not change the function
signatures.
"""


def _ledger_mutations(p: dict) -> list[tuple[str, list]]:
    BOUNDARY = ("if balance - amount < FLOOR:\n                rejected += 1\n"
                "                continue\n            balance -= amount",
                "if balance - amount <= FLOOR:\n                rejected += 1\n"
                "                continue\n            balance -= amount")
    NO_SKIP = ("                rejected += 1\n                continue\n"
               "            balance -= amount",
               "                rejected += 1\n            balance -= amount")
    OPENING = ("if balance - amount < FLOOR:", "if opening - amount < FLOOR:")
    NO_COUNT = ("                rejected += 1\n                continue",
                "                continue")
    muts: list[tuple[str, list]] = [
        ("boundary", [BOUNDARY]),
        ("no-skip", [NO_SKIP]),
        ("opening", [OPENING]),
        ("no-count", [NO_COUNT]),
        ("pre-debit-check", [("if balance - amount < FLOOR:", "if balance < FLOOR:")]),
    ]
    if p["limit"] != 0:
        FLOOR_ZERO = ("FLOOR = " + str(p["limit"]), "FLOOR = 0")
        muts.append(("floor-zero", [FLOOR_ZERO]))
        # Multi-edit: the constant and the comparison are both wrong, and correcting
        # either one alone still fails -- the fix has to reach two places.
        muts.append(("floor+opening", [FLOOR_ZERO, OPENING]))
    if p["fee_bypasses"]:
        FEE_SIGN = ('elif kind == "fee":\n            balance -= amount',
                    'elif kind == "fee":\n            balance += amount')
        muts.append(("fee-sign", [FEE_SIGN]))
        muts.append(("fee-sign+no-count", [FEE_SIGN, NO_COUNT]))
    else:
        muts.append(("fee-bypass", [
            (f'elif kind == "fee":\n            if balance - amount < {p["limit"]}:\n'
             "                rejected += 1\n                continue\n"
             "            balance -= amount",
             'elif kind == "fee":\n            balance -= amount')]))
    return muts


def _ledger_oracle(p: dict, fn: str, args: tuple) -> Any:
    opening, txns = args
    balance, rejected = opening, 0
    for kind, amount in txns:
        if kind == "credit":
            balance += amount
        elif kind == "debit":
            if balance - amount < p["limit"]:
                rejected += 1
                continue
            balance -= amount
        elif kind == "fee":
            if not p["fee_bypasses"] and balance - amount < p["limit"]:
                rejected += 1
                continue
            balance -= amount
        else:
            raise ValueError(kind)
    return (balance, rejected)


def _ledger_edges(p: dict) -> list[tuple[str, tuple]]:
    u = p["unit"]
    return [
        ("apply", (0, [])),
        ("apply", (100 * u, [("debit", 500 * u)])),               # reject
        ("apply", (500 * u, [("debit", 500 * u)])),               # exact to floor
        ("apply", (100 * u, [("fee", 250 * u)])),                 # fee past the floor
        ("apply", (100 * u, [("debit", 500 * u), ("credit", 900 * u),
                             ("debit", 500 * u)])),
        ("apply", (300 * u, [("fee", 100 * u), ("debit", 250 * u)])),
        ("apply", (1000 * u, [("credit", u), ("debit", u), ("fee", u)])),
    ]


def _ledger_cases(rng: random.Random, p: dict) -> list[tuple[str, tuple]]:
    u = p["unit"]
    out = []
    for _ in range(N_CANDIDATES):
        n = rng.randint(0, 6)
        txns = [(rng.choice(["credit", "debit", "fee"]), rng.randrange(1, 12) * 100 * u)
                for _ in range(n)]
        out.append(("apply", (rng.randrange(0, 20) * 100 * u, txns)))
    return out


# ---------------------------------------- pathgrid -------------------------------------

_D4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
_D8 = _D4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))


def _pathgrid_draw(rng: random.Random) -> dict:
    return {
        "conn": rng.choice([4, 4, 8]),
        "wall": rng.choice(["#", "X", "@"]),
        "rows": rng.randint(3, 6),
        "cols": rng.randint(3, 7),
        "density": rng.choice([0.15, 0.25, 0.35]),
    }


def _pathgrid_render(p: dict) -> str:
    deltas = _D4 if p["conn"] == 4 else _D8
    return f'''"""Shortest path on a grid of open cells and walls."""

from collections import deque

WALL = "{p["wall"]}"
DELTAS = {deltas!r}


def steps(grid, start, goal):
    rows, cols = len(grid), len(grid[0])

    def open_cell(rc):
        r, c = rc
        if not (0 <= r < rows and 0 <= c < cols):
            return False
        return grid[r][c] != WALL

    if not open_cell(start) or not open_cell(goal):
        return -1
    seen = {{start}}
    queue = deque([(start, 0)])
    while queue:
        (r, c), dist = queue.popleft()
        if (r, c) == goal:
            return dist
        for dr, dc in DELTAS:
            nxt = (r + dr, c + dc)
            if nxt not in seen and open_cell(nxt):
                seen.add(nxt)
                queue.append((nxt, dist + 1))
    return -1
'''


def _pathgrid_statement(p: dict) -> str:
    move = ("four-directionally (up, down, left, right)" if p["conn"] == 4
            else "eight-directionally — the four orthogonal moves plus the four diagonals, "
                 "each costing one step")
    return f"""# Task

`pathgrid.py` finds the shortest path length on a rectangular grid.

`steps(grid, start, goal)` takes a list of equal-length strings where `.` is open and
`{p["wall"]}` is a wall, plus `(row, col)` start and goal. Movement is {move}. It returns
the number of steps in a shortest path, or `-1` if the goal is unreachable. A start that
equals the goal is 0 steps. A start or goal on a wall is unreachable.

Something in here is wrong. The smoke tests pass and the module is still incorrect.
Fix `pathgrid.py` so it matches the specification above. Do not change the function
signatures.
"""


def _pathgrid_mutations(p: dict) -> list[tuple[str, list]]:
    deltas = _D4 if p["conn"] == 4 else _D8
    WALLS_OPEN = ("        return grid[r][c] != WALL", "        return True")
    DROP_DIR = (f"DELTAS = {deltas!r}", f"DELTAS = {deltas[:-1]!r}")
    UNREACHABLE = ("queue.append((nxt, dist + 1))\n    return -1",
                   "queue.append((nxt, dist + 1))\n    return 0")
    NO_START = ("if not open_cell(start) or not open_cell(goal):",
                "if not open_cell(goal):")
    muts: list[tuple[str, list]] = [
        ("walls-open", [WALLS_OPEN]),
        ("drop-direction", [DROP_DIR]),
        ("unreachable-zero", [UNREACHABLE]),
        ("no-start-check", [NO_START]),
        ("off-grid", [("        if not (0 <= r < rows and 0 <= c < cols):",
                       "        if not (0 <= r <= rows and 0 <= c <= cols):")]),
        ("dist-flat", [("queue.append((nxt, dist + 1))", "queue.append((nxt, dist))")]),
        # Multi-edit: reachability and the distance it reports are both wrong, and each
        # correction alone still fails.
        ("drop-dir+unreachable", [DROP_DIR, UNREACHABLE]),
        ("walls+no-start", [WALLS_OPEN, NO_START]),
    ]
    if p["conn"] == 4:
        muts.append(("extra-diagonal", [(f"DELTAS = {deltas!r}",
                                         f"DELTAS = {deltas + ((1, 1), (-1, -1))!r}")]))
    else:
        muts.append(("lost-diagonals", [(f"DELTAS = {deltas!r}", f"DELTAS = {_D4!r}")]))
    return muts


def _pathgrid_oracle(p: dict, fn: str, args: tuple) -> Any:
    """Bellman-Ford style relaxation to a fixpoint -- not the BFS under repair."""
    grid, start, goal = args
    rows, cols = len(grid), len(grid[0])

    def openc(rc):
        r, c = rc
        return 0 <= r < rows and 0 <= c < cols and grid[r][c] != p["wall"]

    if not openc(start) or not openc(goal):
        return -1
    deltas = _D4 if p["conn"] == 4 else _D8
    inf = float("inf")
    dist = {(r, c): inf for r in range(rows) for c in range(cols) if openc((r, c))}
    dist[start] = 0
    changed = True
    while changed:
        changed = False
        for (r, c), d in list(dist.items()):
            if d == inf:
                continue
            for dr, dc in deltas:
                n = (r + dr, c + dc)
                if n in dist and dist[n] > d + 1:
                    dist[n] = d + 1
                    changed = True
    return -1 if dist[goal] == inf else dist[goal]


def _grid_from(rows: int, cols: int, wall: str, blocked: set) -> list[str]:
    return ["".join(wall if (r, c) in blocked else "." for c in range(cols))
            for r in range(rows)]


def _pathgrid_edges(p: dict) -> list[tuple[str, tuple]]:
    w = p["wall"]
    open3 = _grid_from(3, 3, w, set())
    return [
        ("steps", (open3, (1, 1), (1, 1))),                              # start == goal
        ("steps", (open3, (2, 0), (0, 2))),                              # corner to corner
        ("steps", (_grid_from(2, 2, w, {(0, 0)}), (0, 0), (1, 1))),      # start on a wall
        ("steps", (_grid_from(2, 2, w, {(0, 1)}), (0, 0), (0, 1))),      # goal on a wall
        ("steps", ([f"...", f"{w}{w}{w}", f"..."], (0, 1), (2, 1))),     # walled off
        ("steps", ([f".{w}.", f".{w}.", f".{w}."], (0, 0), (0, 2))),     # split grid
        ("steps", ([f"....", f".{w}{w}.", f"...."], (0, 0), (2, 3))),    # around a wall
        ("steps", ([".."], (0, 0), (0, 1))),                             # single row
    ]


def _pathgrid_cases(rng: random.Random, p: dict) -> list[tuple[str, tuple]]:
    out = []
    for _ in range(N_CANDIDATES):
        rows = rng.randint(2, p["rows"])
        cols = rng.randint(2, p["cols"])
        blocked = {(r, c) for r in range(rows) for c in range(cols)
                   if rng.random() < p["density"]}
        grid = _grid_from(rows, cols, p["wall"], blocked)
        start = (rng.randrange(rows), rng.randrange(cols))
        goal = (rng.randrange(rows), rng.randrange(cols))
        out.append(("steps", (grid, start, goal)))
    return out


REPAIR_TEMPLATES = [
    _Template("intervals", ("merge", "covered"), _intervals_draw, _intervals_render,
              _intervals_statement, _intervals_mutations, _intervals_oracle,
              _intervals_edges, _intervals_cases),
    _Template("ledger", ("apply",), _ledger_draw, _ledger_render, _ledger_statement,
              _ledger_mutations, _ledger_oracle, _ledger_edges, _ledger_cases),
    _Template("pathgrid", ("steps",), _pathgrid_draw, _pathgrid_render,
              _pathgrid_statement, _pathgrid_mutations, _pathgrid_oracle,
              _pathgrid_edges, _pathgrid_cases),
]


def cell_id(world: "RepairWorld") -> str:
    """The (template, specification, operator) cell an instance came from. Two instances
    in the same cell are not independent draws; this is what makes that auditable instead
    of assumed, and what a report of effective n has to be computed over."""
    d = world.difficulty
    spec = ",".join(f"{k}={v}" for k, v in sorted(d.get("params", {}).items()))
    return f"{d['template']}[{spec}]/{d['mutation']}"


def _render_tests(module: str, entries: tuple[str, ...], header: str,
                  cases: list[tuple[str, tuple, Any]]) -> str:
    lines = [f"from {module} import {', '.join(entries)}", ""]
    for fn, args, want in cases:
        lines.append(f"assert {_render_case(fn, args)} == {want!r}")
    lines += ["", f'print("{header}")', ""]
    return "\n".join(lines)


def _render_hidden(module: str, entries: tuple[str, ...],
                   cases: list[tuple[str, tuple, Any, str]]) -> str:
    head = f'''import sys
sys.path.insert(0, ".")
from {module} import {', '.join(entries)}

_p = _t = 0
def check(got, want, label):
    global _p, _t
    _t += 1
    if got == want:
        _p += 1
    else:
        print(f"FAIL {{label}}: got {{got!r}} want {{want!r}}")

'''
    body = "\n".join(f"check({_render_case(fn, args)}, {want!r}, {label!r})"
                     for fn, args, want, label in cases)
    return head + body + '''
print(f"CASES {_p} {_t}")
sys.exit(0 if _p == _t else 1)
'''


def generate(seed: int, template: str | None = None) -> RepairWorld:
    """Draw one repair instance.

    The specification, the constants, the test inputs and the mutation operator are all
    drawn from `seed`. `template` pins the module family; otherwise it too is seeded.

    Raises `AssertionError` if the reference module disagrees with the independent oracle,
    or if no mutation operator leaves the bug both invisible to the smoke suite and
    visible to the hidden one -- the two properties the whole design rests on.
    """
    rng = random.Random(seed)
    pool = [t for t in REPAIR_TEMPLATES if template in (None, t.name)]
    if not pool:
        raise KeyError(template)
    tpl = rng.choice(pool)

    params = tpl.draw(rng)
    reference = tpl.render(params)
    ref_ns = _load(reference, tpl.name)

    edges = tpl.edges(params)
    drawn = tpl.cases(rng, params)
    want = {i: ("ok", tpl.oracle(params, fn, args))
            for i, (fn, args) in enumerate(edges + drawn)}

    # The reference has to agree with the independent oracle everywhere, or the oracle is
    # measuring its own bugs -- probe property 3, kept real rather than tautological.
    for i, (fn, args) in enumerate(edges + drawn):
        got = _call(ref_ns, fn, args)
        if got != want[i]:
            raise AssertionError(
                f"{tpl.name} seed={seed}: reference disagrees with the oracle on "
                f"{_render_case(fn, args)}: reference {got!r}, oracle {want[i]!r}")

    all_muts = tpl.mutations(params)
    order = list(range(len(all_muts)))
    rng.shuffle(order)
    # Single-edit operators outnumber multi-edit ones, so an unbiased draw yields ~18%
    # multi-edit and barely moves difficulty. MULTI_EDIT_RATE is the fraction of seeds
    # that prefer a multi-edit defect; the rest are single-edit, so the pool spans both.
    if rng.random() < MULTI_EDIT_RATE:
        order.sort(key=lambda i: len(all_muts[i][1]) < 2)
    def _apply(edits: list) -> str:
        out = reference
        for find, replace in edits:
            if find not in out:
                raise AssertionError(
                    f"{tpl.name}: mutation edit no longer matches its rendered source: "
                    f"{find[:60]!r}")
            out = out.replace(find, replace, 1)
        return out

    for op_index in order:
        label, edits = tpl.mutations(params)[op_index]
        buggy = _apply(edits)
        try:
            bug_ns = _load(buggy, tpl.name)
        except Exception:                                        # noqa: BLE001
            continue                                             # mutant does not import

        n_edges = len(edges)
        agree, differ = [], []
        for i, (fn, args) in enumerate(edges + drawn):
            got = _call(bug_ns, fn, args)
            (agree if got == want[i] else differ).append(i)

        # Visible cases must come from the drawn pool, never the spec corners: a smoke
        # suite built from corner cases would hand the agent the specification's edges
        # for free, which is most of the task.
        #
        # Balanced across entry points where possible. A mutation localised to one
        # function means no passing case can call it, so an unbalanced smoke suite tells
        # the agent which function is broken -- on a two-function module that is most of
        # the search. Taking one agreeing case per entry point first shrinks that tell
        # without weakening the "smoke passes on the mutant" property, which still holds
        # by construction. It cannot always be removed: if every call to a function
        # disagrees, no case exists to include.
        pool_i = [i for i in agree if i >= n_edges]
        vis, taken = [], set()
        for i in pool_i:
            fn = (edges + drawn)[i][0]
            if fn not in taken:
                taken.add(fn)
                vis.append(i)
        vis += [i for i in pool_i if i not in vis]
        vis = vis[:4]
        # Hidden = every spec corner, plus drawn cases that separate the mutant.
        hid = list(range(n_edges)) + [i for i in differ if i >= n_edges][:4]
        if len(vis) < MIN_VISIBLE or len([i for i in differ if i in hid]) < MIN_DISCRIMINATING:
            continue

        # A multi-edit defect has to actually require every edit. Revert one at a time:
        # if the module passes the hidden suite with any single edit undone, the other
        # edits were decoration and the instance is a single-edit task wearing a longer
        # label. Reject the operator rather than mislabel the difficulty.
        if len(edits) > 1:
            def _still_fails(subset: list) -> bool:
                try:
                    pns = _load(_apply(subset), tpl.name)
                except Exception:                                # noqa: BLE001
                    return True
                return any(_call(pns, *(edges + drawn)[i]) != want[i] for i in hid)

            if not all(_still_fails([e for j, e in enumerate(edits) if j != skip])
                       for skip in range(len(edits))):
                continue

        def _c(i: int) -> tuple[str, tuple]:
            return (edges + drawn)[i]

        visible_src = _render_tests(
            tpl.name, tpl.entries, "smoke ok",
            [(*_c(i), want[i][1]) for i in vis])
        hidden_src = _render_hidden(
            tpl.name, tpl.entries,
            [(*_c(i), want[i][1], f"case{i}") for i in hid])

        return RepairWorld(
            task_id=f"repair-{tpl.name}-{seed}",
            family="repair",
            seed=seed,
            statement=tpl.statement(params),
            module_name=tpl.name,
            buggy_source=buggy,
            reference_source=reference,
            visible_tests=visible_src,
            hidden_tests=hidden_src,
            hidden_cases=len(hid),
            difficulty={"template": tpl.name, "mutation": label, "params": params,
                        "edits": len(edits),
                        "hidden_cases": len(hid), "visible_cases": len(vis),
                        "discriminating": len([i for i in differ if i in hid])},
        )

    raise AssertionError(
        f"{tpl.name} seed={seed} params={params}: no mutation operator leaves the bug both "
        "invisible to the smoke suite and visible to the hidden suite")
