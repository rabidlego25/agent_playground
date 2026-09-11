from ledger import apply

def test_apply():
    # Test credits
    assert apply(1000, [("credit", 500)]) == (1500, 0)
    
    # Test debits under floor
    # FLOOR = -2000
    # balance = 0, debit 2500 -> 0 - 2500 = -2500 < -2000, rejected
    assert apply(0, [("debit", 2500)]) == (0, 1)
    
    # Test debits exactly at floor
    # balance = 0, debit 2000 -> 0 - 2000 = -2000 == FLOOR (allowed? "below the overdraft floor of -2000 cents is rejected")
    # "below" means strictly less than -2000? Let's check: balance - amount < -2000 is <. So -2000 is allowed.
    assert apply(0, [("debit", 2000)]) == (-2000, 0)

    # Test fee
    # Fee is always applied even if it takes balance past floor
    assert apply(-1900, [("fee", 300)]) == (-2200, 0)

    # Test incrementing rejected count
    assert apply(0, [("debit", 2500), ("debit", 1000)]) == (-1000, 1)
    
    # Test multiple types
    bal, rej = apply(1000, [("debit", 4000), ("fee", 100), ("credit", 500)])
    # debit 4000: 1000 - 4000 = -3000 < -2000 -> rejected, rejected=1, balance=1000
    # fee 100: balance = 1000 + 100 = 1100 (wait, fee in ledger.py does `balance += amount`? Wait! Is fee positive or negative? Or does fee subtract or add? Wait, let's check what a fee is!)
    # Ah, let's look at `ledger.py`: `elif kind == "fee": balance += amount`? Wait, fee is a charge, so does it subtract or add? Or are fee amounts positive and fees subtract from balance?)
