from pathgrid import steps

assert steps(['......', 'X....X', '...X..'], (2, 5), (0, 2)) == 5
assert steps(['...X...', '...XX..'], (1, 6), (0, 5)) == 2
assert steps(['.....X', '.X....', '......'], (1, 5), (0, 2)) == 4
assert steps(['X..', '...'], (0, 2), (0, 2)) == 0

print("smoke ok")
