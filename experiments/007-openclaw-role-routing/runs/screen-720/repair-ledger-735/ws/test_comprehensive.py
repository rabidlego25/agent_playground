from ledger import apply

def test_debit_against_running_balance():
    # Opening is 100.
    # Credit 50 -> balance 150.
    # Debit 120 -> balance would be 30, which is >= 0, should succeed -> balance 30.
    # Debit 50 -> balance would be -20 (< 0), should be rejected -> balance 30, rejected 1.
    balance, rejected = apply(100, [("credit", 50), ("debit", 120), ("debit", 50)])
    assert balance == 30
    assert rejected == 1

def test_fee_below_zero():
    # Opening 10.
    # Debit 20 -> rejected (balance would be -10).
    # Fee 20 -> applied (fee always applies), balance becomes -10.
    balance, rejected = apply(10, [("debit", 20), ("fee", 20)])
    assert balance == -10
    assert rejected == 1

if __name__ == "__main__":
    test_debit_against_running_balance()
    test_fee_below_zero()
    print("All additional tests passed!")
