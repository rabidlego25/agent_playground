from intervals import merge, covered

assert merge([(9, 13), (18, 22)]) == [(9, 13), (18, 22)]
assert covered([(14, 15), (14, 16), (17, 20), (19, 20), (19, 20)]) == 5
assert covered([(17, 18)]) == 1
assert covered([(0, 2), (15, 19), (16, 21), (15, 17)]) == 8

print("smoke ok")
