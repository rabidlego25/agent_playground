"""Shortest path on a grid of open cells and walls."""

from collections import deque

WALL = "#"
DELTAS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def steps(grid, start, goal):
    rows, cols = len(grid), len(grid[0])

    def open_cell(rc):
        r, c = rc
        if not (0 <= r < rows and 0 <= c < cols):
            return False
        return grid[r][c] != WALL

    if not open_cell(start) or not open_cell(goal):
        return -1
    seen = {start}
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
