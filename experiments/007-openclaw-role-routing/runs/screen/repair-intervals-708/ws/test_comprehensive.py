from intervals import merge, covered

def test_intervals():
    # Touching intervals should remain separate
    assert merge([(1, 3), (3, 5)]) == [(1, 3), (3, 5)]
    
    # Overlapping intervals should merge
    assert merge([(1, 3), (2, 4)]) == [(1, 4)]
    
    # Unordered inputs
    assert merge([(3, 5), (1, 3)]) == [(1, 3), (3, 5)]

test_intervals()
print("all tests passed")
