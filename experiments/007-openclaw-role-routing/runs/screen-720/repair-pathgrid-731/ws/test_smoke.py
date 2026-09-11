from pathgrid import steps

assert steps(['..', '..', '..'], (0, 1), (0, 1)) == 0
assert steps(['@.@', '@.@', '...'], (1, 2), (1, 2)) == -1
assert steps(['..@', '...'], (0, 2), (1, 1)) == -1
assert steps(['...', '...'], (0, 0), (0, 0)) == 0

print("smoke ok")
