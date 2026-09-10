from ledger import apply

def test_all():
    # Smoke tests
    assert apply(35000, [('debit', 20000), ('debit', 10000), ('fee', 2500), ('debit', 27500), ('credit', 5000)]) == (7500, 1)
    assert apply(32500, []) == (32500, 0)
    assert apply(42500, [('credit', 20000), ('credit', 25000)]) == (87500, 0)
    assert apply(47500, [('credit', 25000), ('debit', 2500), ('credit', 20000), ('credit', 7500)]) == (97500, 0)

    # Fee taking balance past floor
    assert apply(1000, [('fee', 1500)]) == (1000, 1)
    
    # Debit taking balance past floor
    assert apply(1000, [('debit', 1500)]) == (1000, 0)

    print("All tests passed successfully!")

if __name__ == "__main__":
    test_all()
