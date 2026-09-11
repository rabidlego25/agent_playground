# Task

`pathgrid.py` finds the shortest path length on a rectangular grid.

`steps(grid, start, goal)` takes a list of equal-length strings where `.` is open and
`#` is a wall, plus `(row, col)` start and goal. Movement is four-directionally (up, down, left, right). It returns
the number of steps in a shortest path, or `-1` if the goal is unreachable. A start that
equals the goal is 0 steps. A start or goal on a wall is unreachable.

Something in here is wrong. The smoke tests pass and the module is still incorrect.
Fix `pathgrid.py` so it matches the specification above. Do not change the function
signatures.
