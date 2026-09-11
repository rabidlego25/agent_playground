from toolkit import merge, covered
from toolkit import steps
from toolkit import apply
assert merge([(55, 65), (40, 65), (70, 80), (45, 55), (85, 105)]) == [(40, 65), (70, 80), (85, 105)]
assert merge([(75, 90), (20, 25), (25, 40), (85, 100)]) == [(20, 25), (25, 40), (75, 100)]
assert merge([(5, 30), (10, 25), (15, 30), (65, 70)]) == [(5, 30), (65, 70)]
assert merge([(5, 30), (50, 75)]) == [(5, 30), (50, 75)]
assert steps(['...@.', '@....', '...@.', '.@...'], (1, 1), (0, 1)) == 1
assert steps(['@.....', '@..@.@', '...@..', '..@@..'], (0, 1), (2, 2)) == 2
assert steps(['...@..', '@.....', '..@.@.'], (2, 0), (0, 4)) == 4
assert steps(['...', '.@.'], (0, 2), (0, 1)) == 1
assert apply(0, [('credit', 20000), ('debit', 22500)]) == (20000, 1)
assert apply(30000, [('fee', 15000), ('debit', 15000), ('debit', 25000), ('debit', 17500)]) == (0, 2)
assert apply(40000, [('credit', 15000), ('credit', 10000), ('debit', 20000), ('fee', 20000)]) == (25000, 0)
assert apply(47500, [('credit', 25000), ('debit', 27500)]) == (45000, 0)

print("smoke ok")
