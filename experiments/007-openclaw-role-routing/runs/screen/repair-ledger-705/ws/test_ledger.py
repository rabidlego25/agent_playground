import unittest
from ledger import apply

class TestLedger(unittest.TestCase):
    def test_credit(self):
        self.assertEqual(apply(1000, [("credit", 500)]), (1500, 0))

    def test_debit_normal(self):
        self.assertEqual(apply(1000, [("debit", 400)]), (600, 0))

    def test_debit_to_zero(self):
        # Balance 100, debit 100 -> balance becomes 0. 0 is not below zero.
        self.assertEqual(apply(100, [("debit", 100)]), (0, 0))

    def test_debit_below_zero(self):
        # Balance 100, debit 101 -> balance would be -1, which is below zero. Rejected.
        self.assertEqual(apply(100, [("debit", 101)]), (100, 1))

    def test_fee_into_overdraft(self):
        # "A fee is always applied, even into overdraft."
        self.assertEqual(apply(50, [("fee", 100)]), (-50, 0))

if __name__ == "__main__":
    unittest.main()
