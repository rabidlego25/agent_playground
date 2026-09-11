from intervals import merge, covered

assert covered([(160, 210)]) == 50
assert merge([(150, 190)]) == [(150, 190)]
assert merge([(80, 120)]) == [(80, 120)]
assert covered([(210, 240), (200, 240), (80, 120), (140, 160), (170, 210)]) == 130

print("smoke ok")
