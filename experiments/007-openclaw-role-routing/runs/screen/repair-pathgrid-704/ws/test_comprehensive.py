from pathgrid import steps

def test_all():
    assert steps(['...@', '..@.', '....', '@...'], (3, 1), (0, 1)) == 3
    assert steps(['@.', '..', '..'], (0, 1), (1, 0)) == 2
    assert steps(['.@..', '....'], (0, 2), (0, 2)) == 0
    assert steps(['.@@', '...', '...', '.@.', '@..'], (4, 1), (3, 2)) == 2
    # Test wall start/goal
    assert steps(['@.', '..'], (0, 0), (1, 1)) == -1
    assert steps(['.@', '..'], (0, 1), (1, 0)) == -1
    # Test wall on path
    assert steps(['.@', '.@'], (0, 0), (1, 0)) == -1
    print("all tests passed")

if __name__ == '__main__':
    test_all()
