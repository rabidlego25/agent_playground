# Task

`ledger.py` applies a list of transactions to an opening balance.

`apply(opening, txns)` processes each `(kind, amount)` in order. `kind` is `"credit"`,
`"debit"` or `"fee"`. A debit that would take the balance below zero is rejected and
skipped entirely. A fee is always applied, even into overdraft. `apply` returns
`(balance, rejected)` where `rejected` is the count of skipped debits. All amounts are
in whole cents; the balance is an int throughout.

Something in here is wrong. The smoke tests pass and the module is still incorrect.
Fix `ledger.py` so it matches the specification above. Do not change the function
signatures.
