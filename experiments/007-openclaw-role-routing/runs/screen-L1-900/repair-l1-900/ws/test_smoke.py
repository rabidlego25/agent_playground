from toolkit import steps
from toolkit import merge, covered
from toolkit import apply
assert steps(['@..', '.@@', '...', '...'], (2, 2), (1, 2)) == -1
assert steps(['.@', '@@', '.@', '..', '..'], (2, 1), (1, 0)) == -1
assert steps(['@.', '..'], (1, 1), (0, 0)) == -1
assert steps(['@.', '..'], (0, 1), (0, 0)) == -1
assert covered([(135, 160)]) == 25
assert merge([(75, 90)]) == [(75, 90)]
assert merge([(20, 25), (45, 65), (65, 80)]) == [(20, 25), (45, 65), (65, 80)]
assert merge([(85, 90)]) == [(85, 90)]
assert apply(400, [('debit', 400), ('credit', 500), ('fee', 300)]) == (200, 0)
assert apply(1100, [('fee', 600)]) == (500, 0)
assert apply(600, []) == (600, 0)
assert apply(1800, [('debit', 1100), ('fee', 400)]) == (300, 0)

print("smoke ok")
