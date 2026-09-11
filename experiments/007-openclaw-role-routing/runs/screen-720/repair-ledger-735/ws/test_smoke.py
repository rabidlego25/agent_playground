from ledger import apply

assert apply(0, [('credit', 40000), ('credit', 60000), ('fee', 20000)]) == (80000, 0)
assert apply(120000, [('credit', 20000), ('debit', 100000), ('credit', 60000), ('fee', 20000), ('fee', 110000)]) == (-30000, 0)
assert apply(110000, [('fee', 60000), ('fee', 30000), ('credit', 100000), ('credit', 70000), ('debit', 100000), ('fee', 90000)]) == (0, 0)
assert apply(0, [('fee', 110000), ('fee', 10000), ('credit', 90000), ('fee', 50000)]) == (-80000, 0)

print("smoke ok")
