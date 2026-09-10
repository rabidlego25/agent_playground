from pathgrid import steps

assert steps(['..', 'XX'], (0, 0), (1, 0)) == -1
assert steps(['...', 'X.X'], (1, 0), (1, 1)) == -1
assert steps(['..', '..'], (0, 1), (0, 0)) == 1
assert steps(['.XX', '...', '.X.'], (0, 1), (0, 1)) == -1

print("smoke ok")
