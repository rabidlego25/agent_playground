from ledger import apply

def test_debit_against_running_balance():
    # Opening 0, debit 1000 -> balance -1000 (valid)
    # Next debit 1500 -> would be -2500, below floor -2000, so rejected.
    balance, rejected = apply(0, [("debit", 1000), ("debit", 1500)])
    assert balance == -1000
    assert rejected == 1

def test_fee_exceeding_floor():
    # Opening -1900, fee 200 -> balance -2100 (allowed for fees)
    balance, rejected = apply(-1900, [("fee", 200)])
    assert balance == -2100
    assert rejected == 0

if __name__ == "__main__":
    test_debit_against_running_balance()
    test_fee_exceeding_floor()
    print("All additional tests passed!")
