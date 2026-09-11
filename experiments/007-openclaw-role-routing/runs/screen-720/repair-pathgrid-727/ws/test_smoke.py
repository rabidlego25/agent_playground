from pathgrid import steps

assert steps(['....', '....'], (0, 1), (1, 0)) == 2
assert steps(['.@@..', '.....'], (0, 4), (0, 2)) == -1
assert steps(['....@', '.....', '.....'], (0, 0), (2, 0)) == 2
assert steps(['..', '..', '..'], (0, 0), (2, 1)) == 3

print("smoke ok")
