from pathgrid import steps

def test_all():
    assert steps(['...', '...', '.#.', '#..'], (1, 2), (2, 1)) == -1
    assert steps(['.#', '..', '..', '..'], (1, 0), (3, 0)) == 2
    assert steps(['.##.', '...#', '#...', '.##.'], (1, 0), (1, 3)) == -1
    assert steps(['.#', '.#', '#.'], (0, 1), (0, 0)) == -1
    # Check left movement
    assert steps(['...', '...', '...'], (1, 2), (1, 0)) == 2
    # Check start == goal
    assert steps(['...'], (0, 1), (0, 1)) == 0
    # Check wall start/goal
    assert steps(['.#.'], (0, 1), (0, 0)) == -1

if __name__ == '__main__':
    test_all()
    print("all tests passed")
