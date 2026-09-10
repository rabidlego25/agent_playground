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

Contamination resistance comes from generation: the defect, its location and the
constants are drawn per seed, so there is no fixed corpus to have memorized.

**The hidden tests never touch the workspace.** An agent with write access can edit any
file it can see, including a test that judges it. `check()` copies the workspace to a
temporary directory, writes the hidden suite there, and runs it out of the agent's reach.
"""

from __future__ import annotations

import os
import random
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

__all__ = ["generate", "RepairWorld", "Verdict", "REPAIR_TEMPLATES"]


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
        return self.hidden_tests.count("check(") - 1     # the definition is not a case


# --------------------------------------------------------------------------------------
# Templates. Each is a correct module, a visible suite that passes on the mutated code,
# a hidden suite that does not, and mutation operators that are plausible human errors
# rather than random token damage.
# --------------------------------------------------------------------------------------

_INTERVALS = {
    "name": "intervals",
    "statement": """# Task

`intervals.py` merges overlapping closed intervals and reports total coverage.

`merge(spans)` takes a list of `(start, end)` pairs and returns them merged and sorted,
with touching intervals (`(1, 3)` and `(3, 5)`) counted as overlapping and combined.
`covered(spans)` returns the total length covered, counting overlap once.

Something in here is wrong. The smoke tests pass and the module is still incorrect.
Fix `intervals.py` so it matches the specification above. Do not change the function
signatures.
""",
    "source": '''"""Merge overlapping closed intervals."""


def merge(spans):
    if not spans:
        return []
    ordered = sorted(spans, key=lambda s: s[0])
    out = [list(ordered[0])]
    for start, end in ordered[1:]:
        if start <= out[-1][1]:
            out[-1][1] = max(out[-1][1], end)
        else:
            out.append([start, end])
    return [tuple(s) for s in out]


def covered(spans):
    return sum(end - start for start, end in merge(spans))
''',
    "visible": '''from intervals import merge, covered

assert merge([(1, 2), (5, 6)]) == [(1, 2), (5, 6)]
assert covered([(1, 2), (5, 6)]) == 2
print("smoke ok")
''',
    "hidden": '''import sys
sys.path.insert(0, ".")
from intervals import merge, covered

_p = _t = 0
def check(got, want, label):
    global _p, _t
    _t += 1
    if got == want:
        _p += 1
    else:
        print(f"FAIL {label}: got {got!r} want {want!r}")

check(merge([(1, 3), (2, 6), (8, 10)]), [(1, 6), (8, 10)], "overlap")
check(merge([(1, 3), (3, 5)]), [(1, 5)], "touching")
check(merge([(5, 6), (1, 2)]), [(1, 2), (5, 6)], "unsorted")
check(merge([(1, 10), (2, 3)]), [(1, 10)], "contained")
check(merge([]), [], "empty")
check(covered([(1, 3), (2, 6)]), 5, "covered-overlap")
check(covered([(1, 3), (3, 5)]), 4, "covered-touching")
check(covered([(0, 4), (1, 2), (6, 7)]), 5, "covered-contained")
print(f"CASES {_p} {_t}")
sys.exit(0 if _p == _t else 1)
''',
    "mutations": [
        ("if start <= out[-1][1]:", "if start < out[-1][1]:"),
        ("out[-1][1] = max(out[-1][1], end)", "out[-1][1] = end"),
        ("ordered = sorted(spans, key=lambda s: s[0])", "ordered = list(spans)"),
        ("return sum(end - start for start, end in merge(spans))",
         "return sum(end - start for start, end in spans)"),
    ],
}

_LEDGER = {
    "name": "ledger",
    "statement": """# Task

`ledger.py` applies a list of transactions to an opening balance.

`apply(opening, txns)` processes each `(kind, amount)` in order. `kind` is `"credit"`,
`"debit"` or `"fee"`. A debit that would take the balance below zero is rejected and
skipped entirely. A fee is always applied, even into overdraft. `apply` returns
`(balance, rejected)` where `rejected` is the count of skipped debits. All amounts are
in whole cents; the balance is an int throughout.

Something in here is wrong. The smoke tests pass and the module is still incorrect.
Fix `ledger.py` so it matches the specification above. Do not change the function
signatures.
""",
    "source": '''"""Apply transactions to an opening balance, in whole cents."""


def apply(opening, txns):
    balance = opening
    rejected = 0
    for kind, amount in txns:
        if kind == "credit":
            balance += amount
        elif kind == "debit":
            if balance - amount < 0:
                rejected += 1
                continue
            balance -= amount
        elif kind == "fee":
            balance -= amount
        else:
            raise ValueError(kind)
    return balance, rejected
''',
    "visible": '''from ledger import apply

assert apply(1000, [("credit", 500)]) == (1500, 0)
assert apply(1000, [("debit", 250)]) == (750, 0)
print("smoke ok")
''',
    "hidden": '''import sys
sys.path.insert(0, ".")
from ledger import apply

_p = _t = 0
def check(got, want, label):
    global _p, _t
    _t += 1
    if got == want:
        _p += 1
    else:
        print(f"FAIL {label}: got {got!r} want {want!r}")

check(apply(100, [("debit", 500)]), (100, 1), "reject-overdraw")
check(apply(500, [("debit", 500)]), (0, 0), "exact-to-zero")
check(apply(100, [("fee", 250)]), (-150, 0), "fee-into-overdraft")
check(apply(100, [("debit", 500), ("credit", 900), ("debit", 500)]), (500, 1), "reject-then-allow")
check(apply(0, []), (0, 0), "empty")
check(apply(300, [("fee", 100), ("debit", 250)]), (200, 1), "fee-then-reject")
check(apply(1000, [("credit", 1), ("debit", 1), ("fee", 1)]), (999, 0), "one-of-each")
print(f"CASES {_p} {_t}")
sys.exit(0 if _p == _t else 1)
''',
    "mutations": [
        ("if balance - amount < 0:", "if balance - amount <= 0:"),
        ("rejected += 1\n                continue", "rejected += 1\n                balance -= amount"),
        ('elif kind == "fee":\n            balance -= amount', 'elif kind == "fee":\n            balance += amount'),
        ("if balance - amount < 0:", "if opening - amount < 0:"),
    ],
}

_GRID = {
    "name": "pathgrid",
    "statement": """# Task

`pathgrid.py` finds the shortest path length on a rectangular grid.

`steps(grid, start, goal)` takes a list of equal-length strings where `.` is open and `#`
is a wall, plus `(row, col)` start and goal. Movement is four-directional. It returns the
number of steps in a shortest path, or `-1` if the goal is unreachable. A start that
equals the goal is 0 steps. A start or goal on a wall is unreachable.

Something in here is wrong. The smoke tests pass and the module is still incorrect.
Fix `pathgrid.py` so it matches the specification above. Do not change the function
signatures.
""",
    "source": '''"""Shortest path on a 4-connected grid of open cells and walls."""

from collections import deque


def steps(grid, start, goal):
    rows, cols = len(grid), len(grid[0])

    def open_cell(rc):
        r, c = rc
        if not (0 <= r < rows and 0 <= c < cols):
            return False
        return grid[r][c] != "#"

    if not open_cell(start) or not open_cell(goal):
        return -1
    seen = {start}
    queue = deque([(start, 0)])
    while queue:
        (r, c), dist = queue.popleft()
        if (r, c) == goal:
            return dist
        for nxt in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if nxt not in seen and open_cell(nxt):
                seen.add(nxt)
                queue.append((nxt, dist + 1))
    return -1
''',
    "visible": '''from pathgrid import steps

assert steps(["...", "...", "..."], (0, 0), (0, 2)) == 2
assert steps(["...", "...", "..."], (1, 1), (1, 1)) == 0
print("smoke ok")
''',
    "hidden": '''import sys
sys.path.insert(0, ".")
from pathgrid import steps

_p = _t = 0
def check(got, want, label):
    global _p, _t
    _t += 1
    if got == want:
        _p += 1
    else:
        print(f"FAIL {label}: got {got!r} want {want!r}")

check(steps(["....", ".##.", "...."], (0, 0), (2, 3)), 5, "around-wall")
check(steps(["..#", "..#", "###"], (0, 0), (0, 2)), -1, "unreachable")
check(steps([".#.", ".#.", ".#."], (0, 0), (0, 2)), -1, "split-grid")
check(steps(["...", "...", "..."], (2, 0), (0, 2)), 4, "diagonal-corner")
check(steps([".."], (0, 0), (0, 1)), 1, "single-row")
check(steps(["#.", ".."], (0, 0), (1, 1)), -1, "start-on-wall")
check(steps([".#", ".."], (0, 0), (0, 1)), -1, "goal-on-wall")
check(steps(["...", "###", "..."], (0, 1), (2, 1)), -1, "walled-off")
print(f"CASES {_p} {_t}")
sys.exit(0 if _p == _t else 1)
''',
    "mutations": [
        # walls stop being walls -- invisible on an open grid, fatal on every walled case
        ('        return grid[r][c] != "#"', "        return True"),
        # a dropped direction: still finds a path, no longer the shortest one
        ("for nxt in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):",
         "for nxt in ((r + 1, c), (r, c + 1), (r, c - 1)):"),
        # diagonals that the specification does not allow
        ("for nxt in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):",
         "for nxt in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1),\n                    (r + 1, c + 1), (r - 1, c - 1)):"),
        # unreachable reported as zero distance rather than -1
        ("queue.append((nxt, dist + 1))\n    return -1",
         "queue.append((nxt, dist + 1))\n    return 0"),
    ],
}

REPAIR_TEMPLATES = [_INTERVALS, _LEDGER, _GRID]


def generate(seed: int, template: str | None = None) -> RepairWorld:
    """Draw one repair instance. `template` pins the module family; otherwise seeded."""
    rng = random.Random(seed)
    pool = [t for t in REPAIR_TEMPLATES if template in (None, t["name"])]
    if not pool:
        raise KeyError(template)
    tpl = rng.choice(pool)
    op_index = rng.randrange(len(tpl["mutations"]))
    find, replace = tpl["mutations"][op_index]
    if find not in tpl["source"]:
        raise AssertionError(f"{tpl['name']} mutation {op_index} no longer matches its source")
    buggy = tpl["source"].replace(find, replace, 1)

    return RepairWorld(
        task_id=f"repair-{tpl['name']}-{seed}",
        family="repair",
        seed=seed,
        statement=tpl["statement"],
        module_name=tpl["name"],
        buggy_source=buggy,
        reference_source=tpl["source"],
        visible_tests=tpl["visible"],
        hidden_tests=tpl["hidden"],
        difficulty={"template": tpl["name"], "mutation": op_index,
                    "hidden_cases": tpl["hidden"].count("check(") - 1},
    )
