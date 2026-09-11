from pathgrid import steps

def test_comprehensive():
    # Corner cases:
    # - start equals goal
    assert steps(['...'], (0, 0), (0, 0)) == 0
    # - start on wall
    assert steps(['#..'], (0, 0), (0, 1)) == -1
    # - goal on wall
    assert steps(['.#.'], (0, 0), (0, 1)) == -1
    # - unreachable
    assert steps(['.#.', '###', '...'], (0, 0), (2, 0)) == -1
    # - diagonal check
    grid = [
        "...",
        "...",
        "..."
    ]
    assert steps(grid, (0, 0), (2, 2)) == 2
    print("comprehensive ok")

if __name__ == '__main__':
    test_comprehensive()
