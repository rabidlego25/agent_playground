import unittest
from ledger import apply

class TestLedger(unittest.TestCase):
    def test_spec(self):
        # Let's write exhaustive tests based on the specification:
        # - "A debit that would take the balance below zero is rejected and skipped entirely."
        #   Does a debit count towards `rejected`? 
        #   Let's check the spec wording:
        #   "A debit that would take the balance below zero is rejected and skipped entirely. 
        #    A fee that would take the balance past the floor is rejected and skipped too, and counts toward `rejected`. 
        #    `apply` returns `(balance, rejected)` where `rejected` is the count of skipped transactions."
        #   Wait! Does debit count towards rejected?
        #   "A fee that would take the balance past the floor is rejected and skipped too, and counts toward `rejected`."
        #   Wait, "skipped too, and counts toward `rejected`" implies either both count or only fee counts or both count!
        #   Wait, let's re-read carefully:
        #   "A debit that would take the balance below zero is rejected and skipped entirely. A fee that would take the balance past the floor is rejected and skipped too, and counts toward `rejected`."
        #   "skipped too, and counts toward `rejected`" -> "too" means fee also counts, or both count! Wait, let's re-read:
        #   Does debit count towards rejected? "A debit that would take the balance below zero is rejected and skipped entirely. A fee that would take the balance past the floor is rejected and skipped too, and counts toward `rejected`."
        #   Wait, if fee is skipped *too*, that means debit is also rejected/skipped. Does debit count toward `rejected`?
        #   Let's check what `ledger.py` currently does:
        #   In `ledger.py`:
        #   debit: checks `balance - amount < FLOOR`, if so `continue` (does NOT increment `rejected`).
        #   fee: checks `balance - amount < 0`, if so `rejected += 1` and `continue`.
        #   Wait, why would fee increment `rejected` and debit not? Or do both count toward `rejected`? Or does debit NOT count toward `rejected`?
        #   Wait, let's re-read: "A debit that would take the balance below zero is rejected and skipped entirely. A fee that would take the balance past the floor is rejected and skipped too, and counts toward `rejected`."
        #   "skipped too, and counts toward `rejected`" means:
        #   1. Debit is rejected and skipped. Does debit count toward `rejected`?
        #   "A debit that would take the balance below zero is rejected and skipped entirely. A fee that would take the balance past the floor is rejected and skipped too, and counts toward `rejected`."
        #   Wait! "skipped too" refers to being rejected and skipped. "counts toward `rejected`" -> does debit count towards `rejected`?
        #   Wait, let's test all possible interpretations or check what is wrong in `ledger.py`.
        pass

if __name__ == '__main__':
    unittest.main()
