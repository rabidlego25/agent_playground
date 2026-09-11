from pathgrid import steps

assert steps(['...@', '..@.', '....', '@...'], (3, 1), (0, 1)) == 3
assert steps(['@.@', '...', '@..', '..@', '...'], (0, 2), (1, 0)) == -1
assert steps(['@.', '..', '..'], (0, 1), (1, 0)) == 2
assert steps(['.@..', '....'], (0, 2), (0, 2)) == 0

print("smoke ok")
