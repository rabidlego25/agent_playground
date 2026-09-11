from ledger import apply

assert apply(12500, [('credit', 10000)]) == (22500, 0)
assert apply(25000, [('credit', 27500), ('credit', 5000), ('fee', 5000), ('fee', 20000), ('credit', 27500)]) == (60000, 0)
assert apply(15000, [('debit', 25000), ('credit', 5000), ('fee', 27500), ('credit', 20000), ('credit', 15000)]) == (55000, 2)
assert apply(10000, [('debit', 15000), ('fee', 22500)]) == (10000, 2)

print("smoke ok")
