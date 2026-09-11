import pytest
from ledger import apply

def test_debit_rejection():
    # A debit that would take the balance below zero is rejected and skipped entirely.
    # Should not decrement balance and should not count toward rejected (wait, does debit count toward rejected? Let's check specification).
    # Specification says: "A debit that would take the balance below zero is rejected and skipped entirely. A fee that would take the balance past the floor is rejected and skipped too, and counts toward rejected. apply returns (balance, rejected) where rejected is the count of skipped transactions."
    # Wait! Let's read carefully: "A debit that would take the balance below zero is rejected and skipped entirely. A fee that would take the balance past the floor is rejected and skipped too, and counts toward `rejected`."
    # Wait, does debit count towards rejected? Or does "counts toward `rejected`" apply only to fee, or both? Let's re-read the spec carefully:
    # "A debit that would take the balance below zero is rejected and skipped entirely. A fee that would take the balance past the floor is rejected and skipped too, and counts toward `rejected`."
    pass
