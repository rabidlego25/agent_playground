from pathgrid import steps

def test_all():
    # 1. Start equals goal
    assert steps(['..', '..'], (0, 0), (0, 0)) == 0

    # 2. Start or goal on a wall
    assert steps(['X.', '..'], (0, 0), (1, 1)) == -1
    assert steps(['..', '.X'], (0, 0), (1, 1)) == -1

    # 3. Simple orthogonal path
    grid1 = [
        "....",
        ".XX.",
        "...."
    ]
    # start (0,0), goal (0,3) -> length 3
    assert steps(grid1, (0, 0), (0, 3)) == 3

    # 4. Diagonal movement
    grid2 = [
        "....",
        "....",
        "...."
    ]
    # (0,0) to (2,2) diagonally in 2 steps
    assert steps(grid2, (0, 0), (2, 2)) == 2

    # 5. Unreachable goal
    grid3 = [
        ".X.",
        "X.X",
        ".X."
    ]
    assert steps(grid3, (0, 0), (2, 2)) == -1

    # 6. Diagonal movement blocked by walls? Wait, does diagonal move check adjacent cells?
    # Usually in grid pathfinding with diagonal moves, can you cut corners through walls?
    # Let's check specification carefully or standard rules.
    # Specification says: "Movement is eight-directionally — the four orthogonal moves plus the four diagonals, each costing one step."
    # Wait, does the code check corner cutting? Let's write tests to verify behavior or check what might be wrong in pathgrid.py.

    print("All additional tests passed!")

if __name__ == '__main__':
    test_all()
