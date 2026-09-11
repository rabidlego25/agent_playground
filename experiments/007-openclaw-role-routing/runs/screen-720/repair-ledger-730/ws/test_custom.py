from ledger import apply

def test_ledger():
    # Test debit skipping and rejection
    # If balance is 100, debit 150 -> below zero -> skipped, balance unchanged (100), rejected count increases by 1?
    # Wait, does debit count towards rejected?
    # Let's re-read: "A debit that would take the balance below zero is rejected and skipped entirely. A fee that would take the balance past the floor is rejected and skipped too, and counts toward `rejected`."
    # Wait! "A fee that would take the balance past the floor is rejected and skipped too, and counts toward `rejected`." -> Does this mean debit does NOT count toward `rejected`, or does "too" mean both do?
    # Let's parse English carefully:
    # "A debit that would take the balance below zero is rejected and skipped entirely. A fee that would take the balance past the floor is rejected and skipped too, and counts toward `rejected`."
    # Wait! "skipped too, and counts toward `rejected`" - wait, does debit count towards rejected or not?
    # Let's re-read the original implementation of debit:
    #         elif kind == "debit":
    #             if balance - amount < FLOOR:
    #                 rejected += 1
    #             balance -= amount
    # Notice that in the original implementation, debit had `rejected += 1`, BUT it did NOT `continue`, so it still executed `balance -= amount` (which was the bug where it executed anyway!).
    # If debit increments `rejected`, why did debit have `rejected += 1` in the original code?
    # Because both debit and fee are rejected when they take the balance below zero / past the floor, and BOTH count toward `rejected`!
    # "A fee that would take the balance past the floor is rejected and skipped too, and counts toward `rejected`." -> "too" means fee is rejected and skipped *too* (just like debit), and counts toward `rejected` (just like debit).
    # Therefore, both debit and fee count toward `rejected` when skipped!
    
    bal, rej = apply(100, [('debit', 150)])
    assert bal == 100
    assert rej == 1

    bal, rej = apply(100, [('fee', 150)])
    assert bal == 100
    assert rej == 1

    print("all tests passed")

if __name__ == '__main__':
    test_ledger()
