from intervals import merge, covered

def test_merge_touching():
    # Touching intervals should remain separate
    assert merge([(1, 3), (3, 5)]) == [(1, 3), (3, 5)]

def test_covered_touching():
    # [1, 3] and [3, 5] cover 1, 2, 3, 4, 5 -> length 5
    assert covered([(1, 3), (3, 5)]) == 5

def test_covered_overlapping():
    # [1, 4] and [3, 6] cover 1, 2, 3, 4, 5, 6 -> length 6
    assert covered([(1, 4), (3, 6)]) == 6

if __name__ == "__main__":
    test_merge_touching()
    test_covered_touching()
    test_covered_overlapping()
    print("All tests passed!")
