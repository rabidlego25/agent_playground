import unittest
from ledger import apply

class LedgerTest(unittest.TestCase):
    def test_fee_rejection(self):
        balance, rejected = apply(100, [("fee", 150)])
        self.assertEqual(balance, 100)
        self.assertEqual(rejected, 1)

    def test_debit_rejection(self):
        balance, rejected = apply(100, [("debit", 150)])
        self.assertEqual(balance, 100)
        self.assertEqual(rejected, 1)

    def test_credit(self):
        balance, rejected = apply(100, [("credit", 50)])
        self.assertEqual(balance, 150)
        self.assertEqual(rejected, 0)

if __name__ == '__main__':
    unittest.main()
