import pytest
from ledger import apply

def test_ledger_specification():
    # Let's check specifications carefully:
    # `apply(opening, txns)` processes each `(kind, amount)` in order.
    # `kind` is `"credit"`, `"debit"` or `"fee"`.
    # A debit that would take the balance below the overdraft floor of -500 cents is rejected and skipped entirely.
    # A fee that would take the balance past the floor is rejected and skipped too, and counts toward `rejected`.
    # `apply` returns `(balance, rejected)` where `rejected` is the count of skipped transactions.
    # Wait, let's re-read carefully:
    # "A debit that would take the balance below the overdraft floor of -500 cents is rejected and skipped entirely."
    # Does a debit count toward `rejected`?
    # Wait! Let's re-read the prompt text:
    # "A debit that would take the balance below the overdraft floor of -500 cents is rejected and skipped entirely. A fee that would take the balance past the floor is rejected and skipped too, and counts toward `rejected`. `apply` returns `(balance, rejected)` where `rejected` is the count of skipped transactions."
    # Wait, does "counts toward `rejected`" apply only to fees, or both debits and fees?
    # Let's re-read:
    # "A debit that would take the balance below the overdraft floor of -500 cents is rejected and skipped entirely. A fee that would take the balance past the floor is rejected and skipped too, and counts toward `rejected`. `apply` returns `(balance, rejected)` where `rejected` is the count of skipped transactions."
    # Wait! "skipped too, and counts toward `rejected`" - does debit count towards rejected?
    # Let's re-read test_smoke.py:
    # `assert apply(400, [('debit', 1100), ('fee', 700), ('fee', 200), ('credit', 600), ('debit', 900), ('fee', 800)]) == (100, 3)`
    # Let's trace `apply(400, [('debit', 1100), ('fee', 700), ('fee', 200), ('credit', 600), ('debit', 900), ('fee', 800)])`:
    # opening = 400
    # 1. debit 1100: balance becomes 400 - 1100 = -700. -700 < -500 (floor), so rejected! Does this count towards rejected?
    # If rejected is 3 total:
    # Let's trace all txns:
    # - debit 1100: 400 - 1100 = -700 (below floor -500) -> rejected (1)
    # - fee 700: current balance 400. 400 - 700 = -300. -300 is NOT below/past -500 (since -300 >= -500). Wait! 400 - 700 = -300, is -300 allowed? Floor is -500. -300 is above -500. Wait, what about fee 700? 400 - 700 = -300. Then balance = -300.
    # - fee 200: balance -300 - 200 = -500. Is -500 allowed? "below the overdraft floor of -500 cents" / "past the floor". Wait, if balance is -500, is it below/past -500?
    # Let's check ledger.py current code for fee: `if balance - amount < -500:` vs debit: `if balance - amount <= FLOOR:` (which is -500).
    # Wait! In current ledger.py:
    # debit checks `balance - amount <= FLOOR` (wait, or `< FLOOR`?)
    # fee checks `balance - amount < -500`
    # Let's check the test case: `apply(400, [('debit', 1100), ('fee', 700), ('fee', 200), ('credit', 600), ('debit', 900), ('fee', 800)]) == (100, 3)`
    pass
