from ledger import apply

assert apply(140000, [('fee', 80000), ('credit', 30000), ('debit', 50000), ('fee', 40000)]) == (0, 0)
assert apply(130000, [('fee', 100000), ('credit', 20000), ('fee', 60000), ('credit', 60000), ('debit', 40000)]) == (70000, 1)
assert apply(150000, [('fee', 50000), ('credit', 110000), ('fee', 20000)]) == (190000, 0)
assert apply(60000, [('credit', 70000), ('fee', 110000), ('credit', 90000), ('fee', 50000), ('fee', 80000)]) == (60000, 1)

print("smoke ok")
