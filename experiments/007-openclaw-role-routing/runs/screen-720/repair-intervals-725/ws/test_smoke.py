from intervals import merge, covered

assert covered([(0, 1), (8, 13)]) == 6
assert merge([(11, 14), (10, 14), (11, 14), (10, 12)]) == [(10, 14)]
assert covered([(5, 8), (5, 9)]) == 4
assert covered([(9, 14)]) == 5

print("smoke ok")
