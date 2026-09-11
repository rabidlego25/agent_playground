from ledger import apply

assert apply(42500, [('debit', 17500)]) == (25000, 0)
assert apply(47500, [('debit', 27500), ('fee', 15000)]) == (5000, 0)
assert apply(17500, [('fee', 27500), ('fee', 22500), ('debit', 2500)]) == (15000, 2)
assert apply(27500, []) == (27500, 0)

print("smoke ok")
