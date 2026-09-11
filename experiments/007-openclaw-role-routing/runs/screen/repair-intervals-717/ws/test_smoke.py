from intervals import merge, covered

assert merge([(4, 6), (38, 44)]) == [(4, 6), (38, 44)]
assert merge([(4, 14), (30, 34), (38, 48), (2, 12)]) == [(2, 14), (30, 34), (38, 48)]
assert merge([(34, 44)]) == [(34, 44)]
assert merge([(34, 40), (8, 12)]) == [(8, 12), (34, 40)]

print("smoke ok")
