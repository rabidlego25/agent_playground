# ---- group: intervals ----
"""Merge overlapping closed intervals."""


def merge(spans):
    if not spans:
        return []
    ordered = sorted(spans, key=lambda s: s[0])
    out = [list(ordered[0])]
    for start, end in ordered[1:]:
        if start < out[-1][1]:
            out[-1][1] = max(out[-1][1], end)
        else:
            out.append([start, end])
    return [tuple(s) for s in out]


def covered(spans):
    return sum(end - start + 1 for start, end in merge(spans))


# ---- group: pathgrid ----
"""Shortest path on a grid of open cells and walls."""

from collections import deque

WALL = "@"
DELTAS = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))


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


# ---- group: ledger ----
"""Apply transactions to an opening balance, in whole cents."""

FLOOR = -500


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
        elif kind == "fee":
            if balance - amount < -500:
                rejected += 1
                continue
            balance -= amount
        else:
            raise ValueError(kind)
    return balance, rejected
