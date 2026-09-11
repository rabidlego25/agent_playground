from toolkit import steps
from toolkit import apply
from toolkit import merge, covered
assert steps(['#..', '###', '..#', '...', '.#.'], (2, 0), (4, 2)) == 2
assert steps(['#.#.#.', '......'], (0, 5), (1, 1)) == 4
assert steps(['....', '....'], (0, 3), (1, 2)) == 1
assert steps(['..', '.#'], (0, 1), (0, 0)) == 1
assert apply(300, []) == (300, 0)
assert apply(1700, [('debit', 1100), ('credit', 900), ('fee', 800)]) == (700, 0)
assert apply(1300, [('fee', 800), ('credit', 300), ('fee', 200)]) == (600, 0)
assert apply(1600, []) == (1600, 0)
assert covered([(13, 14), (19, 23), (14, 18)]) == 9
assert merge([(10, 13)]) == [(10, 13)]
assert covered([(1, 2), (5, 8)]) == 4
assert covered([(25, 29), (9, 10)]) == 5

print("smoke ok")
