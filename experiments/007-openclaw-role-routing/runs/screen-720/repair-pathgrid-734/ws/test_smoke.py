from pathgrid import steps

assert steps(['..', '..', 'X.'], (2, 1), (2, 1)) == 0
assert steps(['XXXXX', '.X...', '.X..X', '....X'], (2, 4), (3, 4)) == -1
assert steps(['X.X..', 'XX.XX', 'X.X.X', '..X..', '...X.'], (4, 1), (1, 4)) == -1
assert steps(['..X.X', 'X.X..'], (0, 1), (0, 3)) == -1

print("smoke ok")
