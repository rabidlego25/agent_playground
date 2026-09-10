from intervals import merge, covered

def test_merge():
    # touching intervals should combine: (1, 3) and (3, 5) -> (1, 5)
    assert merge([(1, 3), (3, 5)]) == [(1, 5)]
    # subset intervals: (1, 5) and (2, 4) -> (1, 5)
    assert merge([(1, 5), (2, 4)]) == [(1, 5)]
    # multiple overlaps
    assert merge([(1, 3), (2, 6), (8, 10), (15, 18)]) == [(1, 6), (8, 10), (15, 18)]

def test_covered():
    assert covered([(1, 3), (3, 5)]) == 4  # 1 to 5 is length 4
    assert covered([(1, 2), (5, 6)]) == 2

test_merge()
test_covered()
print("all tests passed")
