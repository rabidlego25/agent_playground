from pathgrid import steps

assert steps(['##..', '.#.#', '.#.#'], (1, 2), (1, 3)) == -1
assert steps(['.##', '...', '##.', '...'], (3, 0), (3, 1)) == 1
assert steps(['#..##', '.###.'], (0, 2), (1, 4)) == -1
assert steps(['..###', '..#..'], (1, 3), (0, 2)) == -1

print("smoke ok")
