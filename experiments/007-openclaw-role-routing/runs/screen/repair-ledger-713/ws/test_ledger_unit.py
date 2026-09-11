import unittest
from ledger import apply

class TestLedger(unittest.TestCase):
    def test_debit_uses_running_balance(self):
        # Opening 0, debit 200 (balance -200 >= -500) -> succeeds, balance = -200
        # Then debit 400 (balance would be -600 < -500) -> rejected
        balance, rejected = apply(0, [('debit', 200), ('debit', 400)])
        self.assertEqual(balance, -200)
        self.assertEqual(rejected, 1)

    def test_debit_opening_vs_running(self):
        # Implementation bug: uses `opening - amount < FLOOR` instead of `balance - amount < FLOOR` for debit.
        # Let's test with opening = -300, credit 300 (balance = 0), then debit 600.
        # Correct running balance: 0 - 600 = -600 < -500 -> rejected.
        # Buggy code checks: opening (-300) - 600 = -900 < -500 -> rejected (wait, in this case both reject).
        # What about opening = 0, credit 300 (balance = 300), debit 700?
        # Correct running balance: 300 - 700 = -400 >= -500 -> succeeds! Balance becomes -400.
        # Buggy code checks: opening (0) - 700 = -700 < -500 -> REJECTS incorrectly!
        balance, rejected = apply(0, [('credit', 300), ('debit', 700)])
        self.assertEqual(balance, -400)
        self.assertEqual(rejected, 0)

    def test_fee_magic_number(self):
        # Fee checks `-500` literal instead of `FLOOR` constant (though they have the same value, using FLOOR is cleaner).
        # Also check running balance for fee. Fee uses `balance - amount < -500`, which correctly uses running balance.
        pass

if __name__ == '__main__':
    unittest.main()
