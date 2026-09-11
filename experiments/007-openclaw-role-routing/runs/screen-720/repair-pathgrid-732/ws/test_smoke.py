from pathgrid import steps

assert steps(['X..', 'X..'], (1, 1), (0, 0)) == -1
assert steps(['X.', '..', '.X'], (0, 1), (1, 1)) == 1
assert steps(['..', '..', 'X.'], (0, 1), (1, 1)) == 1
assert steps(['X..', '..X', '..X'], (0, 0), (0, 2)) == -1

print("smoke ok")
