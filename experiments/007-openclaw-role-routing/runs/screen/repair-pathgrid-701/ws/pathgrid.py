"""Shortest path on a 4-connected grid of open cells and walls."""

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
        for nxt in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1),
                    (r + 1, c + 1), (r - 1, c - 1)):
            if nxt not in seen and open_cell(nxt):
                seen.add(nxt)
                queue.append((nxt, dist + 1))
    return -1
