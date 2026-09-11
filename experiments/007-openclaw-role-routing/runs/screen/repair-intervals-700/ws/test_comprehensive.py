from intervals import merge, covered

def test_all():
    # Test merge sorting and touching intervals
    assert merge([(3, 5), (1, 3)]) == [(1, 5)]
    assert merge([(1, 3), (2, 6), (8, 10), (15, 18)]) == [(1, 6), (8, 10), (15, 18)]
    assert merge([(1, 5), (5, 10)]) == [(1, 10)]
    
    # Test covered with overlapping and touching intervals
    assert covered([(1, 3), (3, 5)]) == 4
    assert covered([(1, 5), (2, 6)]) == 5
    assert covered([(1, 2), (3, 4)]) == 2
    
    print("all tests passed")

if __name__ == "__main__":
    test_all()
