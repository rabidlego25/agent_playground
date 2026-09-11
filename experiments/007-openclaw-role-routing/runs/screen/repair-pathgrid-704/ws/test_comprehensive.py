from pathgrid import steps

def test_all():
    # Smoke tests
    assert steps(['...@', '..@.', '....', '@...'], (3, 1), (0, 1)) == 3
    assert steps(['@.@', '...', '@..', '..@', '...'], (0, 2), (1, 0)) == -1
    assert steps(['@.', '..', '..'], (0, 1), (1, 0)) == 2
    assert steps(['.@..', '....'], (0, 2), (0, 2)) == 0

    # Unreachable goal case where BFS exits loop without finding goal
    # In the current buggy code, if the queue empties without finding goal, it returns 0 instead of -1!
    grid = [
        ".@",
        "@."
    ]
    # start (0, 0), goal (1, 1) should be unreachable because of walls blocking all paths
    assert steps(grid, (0, 0), (1, 1)) == -1

    print("All tests passed!")

if __name__ == "__main__":
    test_all()
