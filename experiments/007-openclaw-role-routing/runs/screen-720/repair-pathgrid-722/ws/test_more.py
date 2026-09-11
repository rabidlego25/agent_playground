from pathgrid import steps

def test_all():
    # 1. Start equals goal
    assert steps(['...'], (0, 0), (0, 0)) == 0
    
    # 2. Start or goal on a wall
    assert steps(['#..'], (0, 0), (0, 1)) == -1
    assert steps(['.#.'], (0, 1), (0, 1)) == -1

    # 3. Eight-directional movement cost
    # Diagonal move directly
    grid = [
        "...",
        "...",
        "..."
    ]
    assert steps(grid, (0, 0), (2, 2)) == 2

    print("all tests passed")

if __name__ == '__main__':
    test_all()
