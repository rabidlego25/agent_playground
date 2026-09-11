from ledger import apply

def test():
    # Let's run the smoke test and see what happens
    res = apply(400, [('debit', 1100), ('fee', 700), ('fee', 200), ('credit', 600), ('debit', 900), ('fee', 800)])
    print("Result:", res)

if __name__ == '__main__':
    test()
