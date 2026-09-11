from ledger import apply

assert apply(1700, [('fee', 300), ('credit', 800), ('credit', 1100)]) == (3300, 0)
assert apply(1300, [('credit', 1100), ('credit', 500), ('fee', 300), ('debit', 600)]) == (2000, 0)
assert apply(400, [('debit', 1100), ('fee', 700), ('fee', 200), ('credit', 600), ('debit', 900), ('fee', 800)]) == (100, 3)
assert apply(1700, []) == (1700, 0)

print("smoke ok")
