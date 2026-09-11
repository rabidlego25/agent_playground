from pathgrid import steps

assert steps(['...', '.XX', 'X..', '...', '..X'], (3, 1), (3, 1)) == 0
assert steps(['.....', 'X....', '.....'], (1, 0), (1, 0)) == -1
assert steps(['..X', '.X.', '...', '...'], (2, 2), (1, 1)) == -1
assert steps(['.....', '.....', '..X..', '....X', 'X...X'], (3, 0), (2, 1)) == 2

print("smoke ok")
