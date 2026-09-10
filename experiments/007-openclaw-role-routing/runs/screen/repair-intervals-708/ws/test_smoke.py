from intervals import merge, covered

assert covered([(50, 55), (25, 40)]) == 20
assert merge([(0, 10), (35, 40)]) == [(0, 10), (35, 40)]
assert covered([(45, 55), (25, 40), (20, 25)]) == 30
assert merge([(40, 50)]) == [(40, 50)]

print("smoke ok")
