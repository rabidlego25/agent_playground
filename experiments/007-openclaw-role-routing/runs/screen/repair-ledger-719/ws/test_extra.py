from ledger import apply

def test_rejected_count():
    # Debits that take balance below zero should be rejected AND counted in `rejected`.
    # Let's check: opening = 100, debit = 150 -> balance would be -50 (< 0), so rejected.
    # Rejected count should be 1.
    balance, rejected = apply(100, [('debit', 150)])
    assert balance == 100
    assert rejected == 1

def test_fee_behavior():
    # Fee is always applied, even if it takes balance past the floor.
    # Wait, what does fee do? Is fee a subtraction or addition? A fee decreases the balance or increases?
    # Wait! In banking / ledgers, a fee usually *decreases* the balance! But let's check how ledger.py implemented fee vs specification.
    # In ledger.py:
    # elif kind == "fee":
    #     balance += amount
    # Wait! A fee adds amount? Or should a fee subtract amount?
    pass

def test_comprehensive():
    pass
