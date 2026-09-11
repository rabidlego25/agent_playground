from ledger import apply

assert apply(30000, [('fee', 80000)]) == (-50000, 0)
assert apply(180000, [('fee', 40000), ('credit', 90000), ('fee', 20000), ('debit', 20000), ('credit', 40000), ('credit', 80000)]) == (310000, 0)
assert apply(70000, []) == (70000, 0)
assert apply(90000, [('fee', 60000), ('fee', 60000), ('fee', 80000), ('fee', 50000), ('credit', 110000), ('credit', 110000)]) == (60000, 0)

print("smoke ok")
