from intervals import merge, covered

assert merge([(30, 35), (40, 45), (15, 25)]) == [(15, 25), (30, 35), (40, 45)]
assert covered([(55, 60), (40, 45)]) == 10
assert merge([(30, 40), (45, 55), (0, 5), (0, 15), (5, 25)]) == [(0, 25), (30, 40), (45, 55)]
assert merge([(40, 50), (40, 50)]) == [(40, 50)]

print("smoke ok")
