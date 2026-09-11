from intervals import merge, covered

assert merge([(45, 65), (30, 40), (45, 60)]) == [(30, 40), (45, 65)]
assert merge([(0, 10), (35, 40)]) == [(0, 10), (35, 40)]
assert merge([(25, 50), (55, 75), (55, 65)]) == [(25, 50), (55, 75)]
assert merge([(40, 65), (0, 5), (45, 65)]) == [(0, 5), (40, 65)]

print("smoke ok")
