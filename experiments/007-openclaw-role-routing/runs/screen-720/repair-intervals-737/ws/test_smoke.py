from intervals import merge, covered

assert merge([(5, 8), (9, 13)]) == [(5, 8), (9, 13)]
assert covered([(3, 5)]) == 2
assert merge([(11, 13), (3, 7)]) == [(3, 7), (11, 13)]
assert merge([(11, 13), (0, 3)]) == [(0, 3), (11, 13)]

print("smoke ok")
