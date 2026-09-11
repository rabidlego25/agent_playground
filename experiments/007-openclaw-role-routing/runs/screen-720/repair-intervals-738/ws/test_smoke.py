from intervals import merge, covered

assert merge([(20, 35), (145, 160)]) == [(20, 35), (145, 160)]
assert covered([(55, 80), (30, 50)]) == 45
assert merge([(15, 35), (85, 95), (135, 145)]) == [(15, 35), (85, 95), (135, 145)]
assert covered([(95, 115), (25, 30), (115, 120), (85, 95)]) == 40

print("smoke ok")
