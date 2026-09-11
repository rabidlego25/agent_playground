from pathgrid import steps

def test_cases():
    # Basic path
    grid = [
        "....",
        ".@@.",
        "...."
    ]
    assert steps(grid, (0, 0), (0, 3)) == 3
    assert steps(grid, (0, 0), (2, 3)) == 5

    # Unreachable
    grid2 = [
        ".@",
        "@."
    ]
    assert steps(grid2, (0, 0), (1, 1)) == -1

if __name__ == "__main__":
    test_cases()
    print("additional tests ok")
