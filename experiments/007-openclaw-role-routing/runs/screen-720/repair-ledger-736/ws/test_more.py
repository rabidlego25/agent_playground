from ledger import apply

def test_full():
    # Test rejection increment and debit rejection
    # opening 100, debit 200 -> rejected
    bal, rej = apply(100, [('debit', 200)])
    assert bal == 100
    assert rej == 1

    # Test fee taking balance below zero
    # opening 50, fee 100 -> balance -50
    bal, rej = apply(50, [('fee', 100)])
    assert bal == -50
    assert rej == 0

    print("all tests passed")

if __name__ == "__main__":
    test_full()
