from intervals import merge, covered

assert covered([(210, 230), (10, 20)]) == 30
assert merge([(180, 190), (210, 260), (290, 340)]) == [(180, 190), (210, 260), (290, 340)]
assert covered([(130, 180), (40, 80), (230, 250)]) == 110
assert covered([(260, 300)]) == 40

print("smoke ok")
