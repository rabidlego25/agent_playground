from pathgrid import steps

assert steps(['...@', '..@.', '....', '@...'], (3, 1), (0, 1)) == 3
assert steps(['@.', '..', '..'], (0, 1), (1, 0)) == 2
assert steps(['.@..', '....'], (0, 2), (0, 2)) == 0
assert steps(['.@@', '...', '...', '.@.', '@..'], (4, 1), (3, 2)) == 2

print("smoke ok")
