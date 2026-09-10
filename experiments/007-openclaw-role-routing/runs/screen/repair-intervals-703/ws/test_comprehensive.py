from intervals import merge, covered

def test_intervals():
    # Smoke tests
    assert merge([(1, 2), (5, 6)]) == [(1, 2), (5, 6)]
    assert covered([(1, 2), (5, 6)]) == 2

    # Touching intervals
    assert merge([(1, 3), (3, 5)]) == [(1, 5)]
    assert covered([(1, 3), (3, 5)]) == 4

    # Unsorted intervals
    assert merge([(5, 6), (1, 2)]) == [(1, 2), (5, 6)]
    assert merge([(3, 5), (1, 3)]) == [(1, 5)]

    # Fully contained intervals
    assert merge([(1, 5), (2, 4)]) == [(1, 5)]

    # Empty
    assert merge([]) == []
    assert covered([]) == 0

    print("All tests passed!")

if __name__ == "__main__":
    test_intervals()
