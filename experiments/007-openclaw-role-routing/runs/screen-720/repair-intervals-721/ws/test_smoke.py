from intervals import merge, covered

assert covered([(28, 36)]) == 8
assert merge([(58, 68)]) == [(58, 68)]
assert covered([(10, 14)]) == 4
assert merge([(40, 44)]) == [(40, 44)]

print("smoke ok")
