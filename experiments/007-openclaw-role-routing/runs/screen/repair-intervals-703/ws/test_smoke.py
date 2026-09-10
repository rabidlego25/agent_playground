from intervals import merge, covered

assert merge([(10, 14), (26, 28)]) == [(10, 14), (26, 28)]
assert covered([(10, 12), (20, 26)]) == 8
assert merge([(30, 38)]) == [(30, 38)]
assert merge([(0, 10), (34, 42)]) == [(0, 10), (34, 42)]

print("smoke ok")
