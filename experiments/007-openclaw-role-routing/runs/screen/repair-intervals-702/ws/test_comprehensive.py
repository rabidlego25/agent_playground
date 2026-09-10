from intervals import merge, covered

def test_merge_unsorted():
    assert merge([(3, 5), (1, 3)]) == [(1, 5)]

def test_merge_touching():
    assert merge([(1, 3), (3, 5)]) == [(1, 5)]

def test_covered_comprehensive():
    assert covered([(1, 3), (3, 5)]) == 4

if __name__ == "__main__":
    test_merge_unsorted()
    test_merge_touching()
    test_covered_comprehensive()
    print("all tests passed")
