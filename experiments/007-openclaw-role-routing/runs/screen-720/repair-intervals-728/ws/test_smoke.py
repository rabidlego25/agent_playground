from intervals import merge, covered

assert merge([(11, 14)]) == [(11, 14)]
assert covered([(11, 12), (28, 31), (2, 7), (17, 22), (7, 11)]) == 18
assert merge([(2, 6), (17, 18)]) == [(2, 6), (17, 18)]
assert merge([(24, 27)]) == [(24, 27)]

print("smoke ok")
