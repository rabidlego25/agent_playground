from pathgrid import steps

assert steps(['@..', '@@.', '@.@', '...', '.@.', '...'], (2, 2), (0, 0)) == -1
assert steps(['..', '..'], (1, 1), (1, 1)) == 0
assert steps(['@.', '..', '.@'], (2, 1), (2, 1)) == -1
assert steps(['.@.', '.@.', '@@.'], (1, 2), (1, 2)) == 0

print("smoke ok")
