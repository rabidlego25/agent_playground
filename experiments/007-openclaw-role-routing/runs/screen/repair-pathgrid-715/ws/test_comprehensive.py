from pathgrid import steps

def test_all():
    # Smoke tests
    assert steps(['..', '..', '..', '..'], (0, 0), (2, 1)) == 3
    assert steps(['...', '#..'], (1, 2), (1, 1)) == 1
    assert steps(['..', '..'], (0, 0), (0, 0)) == 0
    assert steps(['..', '..', '.#'], (1, 0), (1, 0)) == 0

    # Wall check: start on wall or goal on wall should return -1
    assert steps(['#.', '..'], (0, 0), (1, 0)) == -1
    assert steps(['.#', '..'], (0, 1), (1, 0)) == -1

    # Out of bounds start or goal
    assert steps(['..', '..'], (-1, 0), (1, 0)) == -1
    assert steps(['..', '..'], (0, 0), (5, 5)) == -1

    print("All tests passed!")

if __name__ == '__main__':
    test_all()
