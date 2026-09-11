# Task

`ledger.py` applies a list of transactions to an opening balance.

`apply(opening, txns)` processes each `(kind, amount)` in order. `kind` is `"credit"`,
`"debit"` or `"fee"`. A debit that would take the balance below the overdraft floor of -500 cents is rejected and
skipped entirely. A fee that would take the balance past the floor is rejected and skipped too, and counts toward `rejected`. `apply` returns `(balance, rejected)` where `rejected` is the
count of skipped transactions. All amounts are in whole cents; the balance is an int
throughout.

Something in here is wrong. The smoke tests pass and the module is still incorrect.
Fix `ledger.py` so it matches the specification above. Do not change the function
signatures.
