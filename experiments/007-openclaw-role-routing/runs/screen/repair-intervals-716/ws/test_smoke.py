from intervals import merge, covered

assert merge([(20, 28)]) == [(20, 28)]
assert covered([(0, 2), (4, 10)]) == 8
assert merge([(4, 12), (12, 18), (14, 18), (12, 16)]) == [(4, 12), (12, 18)]
assert merge([(0, 2), (0, 10), (16, 24)]) == [(0, 10), (16, 24)]

print("smoke ok")
