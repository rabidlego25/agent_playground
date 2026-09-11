from ledger import apply

assert apply(900, [('credit', 600), ('credit', 800), ('fee', 1000)]) == (1300, 0)
assert apply(200, [('fee', 100)]) == (100, 0)
assert apply(1400, [('credit', 200)]) == (1600, 0)
assert apply(1100, [('debit', 900), ('debit', 900)]) == (-700, 0)

print("smoke ok")
