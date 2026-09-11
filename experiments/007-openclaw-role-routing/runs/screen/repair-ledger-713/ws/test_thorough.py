import pytest
from ledger import apply

def test_debit_checks_running_balance():
    # opening = 100, debit 200 should bring balance to -100, which is >= -500. Should succeed.
    # But wait, check how debit was implemented: `opening - amount < FLOOR`!
    # Let's test debit against running balance vs opening balance.
    # Opening = 0, debit 200 (balance becomes -200 >= -500).
    # If implementation checks `opening - amount < FLOOR`, opening=0 - 200 = -200 < -500 is False, so it passes.
    # But what if opening = -400, and we try to debit 200? Balance would be -600 (< FLOOR).
    # If implementation checks `opening - amount < FLOOR`: -400 - 200 = -600 < -500, so it rejects.
    # BUT what if we had prior transactions that changed the balance?
    # Say opening = 0, credit 200 (balance = 200), then debit 400 (balance becomes 200 - 400 = -200, which is >= -500).
    # If implementation checks `opening - amount < FLOOR`: opening is 0, 0 - 400 = -400. Still passes.
    # But what if opening = -300, credit 300 (balance = 0), then debit 600 (balance becomes -600 < FLOOR)?
    # Implementation checks `opening - amount`: -300 - 600 = -900 < -500, so it rejects even though current balance is 0!
    # Or what if opening = 0, debit 100 (balance = -100), then debit 500 (balance would be -600 < FLOOR)?
    # Implementation checks `opening - amount`: 0 - 500 = -500, not < -500, so it incorrectly ALLOWS it!
    pass

def test_fee_rejection_count():
    # Specification:
    # "A debit that would take the balance below the overdraft floor of -500 cents is rejected and skipped entirely."
    # "A fee that would take the balance past the floor is rejected and skipped too, and counts toward rejected."
    # Wait, does debit count toward rejected?
    # "A debit that would take the balance below the overdraft floor of -500 cents is rejected and skipped entirely. A fee that would take the balance past the floor is rejected and skipped too, and counts toward rejected."
    # Wait! Does a rejected debit count toward `rejected`?
    # Let's re-read carefully:
    # "`apply` returns `(balance, rejected)` where `rejected` is the count of skipped transactions."
    # Wait, does the sentence "counts toward rejected" mean both, or does debit also count? Let's check test_smoke.py.
    # In test_smoke.py:
    # `assert apply(15000, [('debit', 25000), ('credit', 5000), ('fee', 27500), ('credit', 20000), ('credit', 15000)]) == (55000, 2)`
    # Transactions:
    # 1. debit 25000 from 15000 -> balance becomes -10000 -> below -500 -> rejected!
    # 2. credit 5000 -> balance becomes 5000
    # 3. fee 27500 -> balance 5000 - 27500 = -22500 -> below -500 -> rejected!
    # 4. credit 20000 -> balance 25000
    # 5. credit 15000 -> balance 40000... wait, expected result is (55000, 2) with 2 rejections.
    # Let's trace:
    # opening = 15000
    # txn 1: debit 25000 -> rejected (1)
    # txn 2: credit 5000 -> balance = 20000
    # txn 3: fee 27500 -> balance = -7500 -> rejected (2)
    # txn 4: credit 20000 -> balance = 40000
    # txn 5: credit 15000 -> balance = 55000
    # Total rejected = 2 (one debit, one fee). So both debit and fee count toward `rejected`.
