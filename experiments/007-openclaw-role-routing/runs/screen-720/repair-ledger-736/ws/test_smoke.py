from ledger import apply

assert apply(200, []) == (200, 0)
assert apply(1600, [('debit', 700)]) == (900, 0)
assert apply(300, [('credit', 400), ('debit', 300)]) == (400, 0)
assert apply(900, [('debit', 600)]) == (300, 0)

print("smoke ok")
