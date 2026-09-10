from ledger import apply

assert apply(1000, [("credit", 500)]) == (1500, 0)
assert apply(1000, [("debit", 250)]) == (750, 0)
print("smoke ok")
