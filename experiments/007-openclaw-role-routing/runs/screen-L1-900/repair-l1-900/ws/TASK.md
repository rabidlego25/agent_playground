# Task

`toolkit.py` provides 3 independent groups of functions. Each group has its own specification below.

**1 of them contains a defect.** The smoke tests pass and the module is still incorrect. You are not told which group is wrong.

Fix `toolkit.py` so every group matches its specification. Do not change any function signatures.

## Group 1 — `pathgrid`

`pathgrid.py` finds the shortest path length on a rectangular grid.

`steps(grid, start, goal)` takes a list of equal-length strings where `.` is open and
`@` is a wall, plus `(row, col)` start and goal. Movement is eight-directionally — the four orthogonal moves plus the four diagonals, each costing one step. It returns
the number of steps in a shortest path, or `-1` if the goal is unreachable. A start that
equals the goal is 0 steps. A start or goal on a wall is unreachable.

## Group 2 — `intervals`

`intervals.py` merges overlapping closed intervals and reports total coverage.

`merge(spans)` takes a list of `(start, end)` pairs and returns them merged and sorted,
with touching intervals (`(1, 3)` and `(3, 5)`) counted as **separate** — they must overlap by a non-zero amount to be combined.
`covered(spans)` returns the total length covered, counting overlap once.

## Group 3 — `ledger`

`ledger.py` applies a list of transactions to an opening balance.

`apply(opening, txns)` processes each `(kind, amount)` in order. `kind` is `"credit"`,
`"debit"` or `"fee"`. A debit that would take the balance below zero is rejected and
skipped entirely. A fee that would take the balance past the floor is rejected and skipped too, and counts toward `rejected`. `apply` returns `(balance, rejected)` where `rejected` is the
count of skipped transactions. All amounts are in whole cents; the balance is an int
throughout.
