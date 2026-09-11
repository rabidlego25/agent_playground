from ledger import apply

assert apply(45000, []) == (45000, 0)
assert apply(45000, [('debit', 2500), ('credit', 27500)]) == (70000, 0)
assert apply(27500, [('debit', 7500), ('credit', 25000)]) == (45000, 0)
assert apply(12500, []) == (12500, 0)

print("smoke ok")
