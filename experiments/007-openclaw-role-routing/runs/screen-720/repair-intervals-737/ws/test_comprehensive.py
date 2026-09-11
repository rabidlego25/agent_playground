from intervals import merge, covered

def test_intervals():
    # Smoke tests
    assert merge([(5, 8), (9, 13)]) == [(5, 8), (9, 13)]
    assert covered([(3, 5)]) == 2
    assert merge([(11, 13), (3, 7)]) == [(3, 7), (11, 13)]
    assert merge([(11, 13), (0, 3)]) == [(0, 3), (11, 13)]

    # Touching intervals
    assert merge([(1, 3), (3, 5)]) == [(1, 5)]
    assert covered([(1, 3), (3, 5)]) == 4

    # Overlapping intervals
    assert merge([(1, 4), (2, 6)]) == [(1, 6)]
    assert covered([(1, 4), (2, 6)]) == 5

    # Subsumed intervals
    assert merge([(1, 10), (3, 5)]) == [(1, 10)]

    # Unsorted input
    assert merge([(5, 8), (1, 3)]) == [(1, 3), (5, 8)]

    print("All tests passed successfully!")

if __name__ == "__main__":
    test_intervals()
