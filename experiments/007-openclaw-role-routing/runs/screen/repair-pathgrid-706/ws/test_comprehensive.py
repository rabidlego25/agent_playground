from pathgrid import steps

def test_all():
    assert steps(['@..', '@@.', '@.@', '...', '.@.', '...'], (2, 2), (0, 0)) == -1
    assert steps(['..', '..'], (1, 1), (1, 1)) == 0
    assert steps(['@.', '..', '.@'], (2, 1), (2, 1)) == -1
    assert steps(['.@.', '.@.', '@@.'], (1, 2), (1, 2)) == 0
    
    # Additional test cases
    grid = [
        "...",
        ".@.",
        "..."
    ]
    assert steps(grid, (0, 0), (0, 2)) == 2
    assert steps(grid, (0, 0), (2, 2)) == 4
    
    print("all tests passed")

if __name__ == "__main__":
    test_all()
