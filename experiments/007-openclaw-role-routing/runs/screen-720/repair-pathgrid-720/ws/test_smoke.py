from pathgrid import steps

assert steps(['#....', '...#.'], (1, 3), (1, 3)) == -1
assert steps(['..#..', '#.###', '#....', '...#.'], (1, 0), (0, 2)) == -1
assert steps(['##.#', '....', '#.#.', '.##.'], (0, 3), (2, 2)) == -1
assert steps(['#...#.', '#..#..', '.#..##'], (2, 2), (2, 3)) == 1

print("smoke ok")
