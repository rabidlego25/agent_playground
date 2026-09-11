from pathgrid import steps

assert steps(['#....', '.#...', '....#'], (0, 1), (0, 3)) == 2
assert steps(['..#..', '...#.'], (0, 4), (1, 3)) == -1
assert steps(['....', '#...', '....'], (1, 2), (1, 0)) == -1
assert steps(['.....', '.#..#'], (1, 2), (1, 2)) == 0

print("smoke ok")
