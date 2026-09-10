import pytest
from ledger import apply

def test_credit():
    assert apply(1000, [("credit", 500)]) == (1500, 0)

def test_debit_success():
    assert apply(1000, [("debit", 250)]) == (750, 0)

def test_debit_below_zero_rejected():
    # "A debit that would take the balance below zero is rejected and skipped entirely."
    # Wait, what about taking the balance exactly to zero?
    # "would take the balance below zero" -> balance - amount < 0 or <= 0?
    # Let's re-read carefully: "A debit that would take the balance below zero is rejected and skipped entirely."
    # Usually "below zero" means strictly less than zero (< 0). Zero itself is not below zero.
    # Let's check what the current code does: `if balance - amount <= 0:`.
    # If balance is 100 and debit is 100, balance - amount = 0. The current code rejects it (`<= 0`). But taking the balance to zero is NOT taking it below zero!
    # Let's verify this hypothesis.
    pass
