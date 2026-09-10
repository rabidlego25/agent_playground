from intervals import merge, covered

assert merge([(1, 2), (5, 6)]) == [(1, 2), (5, 6)]
assert covered([(1, 2), (5, 6)]) == 2
print("smoke ok")
