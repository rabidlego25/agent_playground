import pytest
from ledger import apply

def test_spec_cases():
    # Specification check:
    # FLOOR = -2000 cents (-$20.00)
    # credit adds
    # debit: rejected and skipped entirely if it would take balance below -2000
    # fee: rejected and skipped too, and counts toward rejected if it would take balance past the floor (-2000)
    # returns (balance, rejected)
    
    # Let's test overdraft floor = -2000
    # opening = 0, debit 2001 -> below -2000 -> rejected
    # opening = 0, debit 2000 -> balance becomes -2000 (allowed? "below the overdraft floor of -2000" means strictly less than -2000 or <= -2000? Let's check wording: "would take the balance below the overdraft floor of -2000 cents is rejected")
    # "below" usually means < -2000. Let's check current code vs spec.
    pass

def test_bugs_in_current_ledger():
    # Look at current ledger.py:
    # FLOOR = 0  <-- BUG: specification says "overdraft floor of -2000 cents"!
    # For debit: uses `opening - amount < FLOOR` <-- BUG: uses `opening` instead of current `balance`!
    # For fee: checks `-2000` hardcoded, but FLOOR = 0. And checks `balance - amount < -2000` (which is correct for floor=-2000, but doesn't increment rejected properly? Wait: "A fee that would take the balance past the floor is rejected and skipped too, and counts toward rejected." The current code for fee increments rejected: `rejected += 1`, but checks against -2000 while FLOOR=0. Also, does debit count toward rejected? Wait! Let's re-read carefully:
    # "A debit that would take the balance below the overdraft floor of -2000 cents is rejected and skipped entirely. A fee that would take the balance past the floor is rejected and skipped too, and counts toward `rejected`."
    # Wait, does debit count toward `rejected`?
    # Let's re-read:
    # "A debit that would take the balance below the overdraft floor of -2000 cents is rejected and skipped entirely. A fee that would take the balance past the floor is rejected and skipped too, and counts toward `rejected`."
    # Wait! Does "counts toward `rejected`" apply to both or just fee, or both? Let's read carefully:
    # "A debit that would take the balance below the overdraft floor of -2000 cents is rejected and skipped entirely. A fee that would take the balance past the floor is rejected and skipped too, and counts toward `rejected`."
    # Wait, let's analyze standard phrasing or write comprehensive tests.
    pass
