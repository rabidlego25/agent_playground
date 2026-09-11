from ledger import apply

assert apply(180000, [('credit', 60000), ('debit', 40000), ('debit', 30000), ('debit', 80000)]) == (90000, 0)
assert apply(120000, []) == (120000, 0)
assert apply(100000, [('credit', 30000)]) == (130000, 0)
assert apply(20000, [('credit', 10000), ('credit', 50000)]) == (80000, 0)

print("smoke ok")
