import unittest
from ledger import apply

class TestLedger(unittest.TestCase):
    def test_debit_floor(self):
        # What if amount is negative? Or credit is negative? Or zero?
        # What about floor check for debit vs fee?
        # In debit: `balance - amount < FLOOR` (FLOOR = 0).
        # In fee: `balance - amount < 0` (0).
        # Wait, what if debit takes balance TO zero? `balance - amount < FLOOR` vs `<= FLOOR`?
        # "A debit that would take the balance below zero is rejected and skipped entirely."
        # Below zero means `< 0`. If balance is 100 and debit is 100, balance becomes 0 (not below zero), so it should be allowed!
        # What about fee? "A fee that would take the balance past the floor is rejected and skipped too"
        # Wait! What is the floor? `FLOOR = 0`. But can a fee take the balance below floor / past the floor? Or can balance go negative for fees or not?
        # Wait, let's re-read:
        # "`ledger.py` applies a list of transactions to an opening balance."
        # "`apply(opening, txns)` processes each `(kind, amount)` in order. `kind` is `"credit"`, `"debit"` or `"fee"`."
        # "A debit that would take the balance below zero is rejected and skipped entirely."
        # "A fee that would take the balance past the floor is rejected and skipped too, and counts toward `rejected`."
        # Wait! Does a debit count toward `rejected`?
        # "A debit that would take the balance below zero is rejected and skipped entirely. A fee that would take the balance past the floor is rejected and skipped too, and counts toward `rejected`."
        # Notice: "skipped too, and counts toward `rejected`". That implies:
        # - Debit is rejected and skipped (does NOT count toward `rejected`? Or DOES count toward `rejected`? Wait, "skipped too" means skipped is shared with debit, but "counts toward `rejected`" is specified for fee? Or does "skipped too, and counts toward `rejected`" mean fee counts toward rejected, while debit does NOT count toward rejected? OR does debit also count toward rejected?)
        # Wait, let's re-read carefully:
        # "A debit that would take the balance below zero is rejected and skipped entirely." (rejected = skipped without incrementing rejected count? Or "rejected" here means action-rejected / ignored?)
        # Wait! Look at the sentence structure:
        # "A debit that would take the balance below zero is rejected and skipped entirely. A fee that would take the balance past the floor is rejected and skipped too, and counts toward `rejected`."
        # Wait, why would one count toward `rejected` and the other not? Or do both count toward `rejected`? Or does debit NOT count toward `rejected`, or DO both count toward `rejected`?
        # Wait, let's re-read: "A fee that would take the balance past the floor is rejected and skipped too, and counts toward `rejected`."
        # Wait, "skipped too" means fee is skipped (like debit). "and counts toward `rejected`" means fee counts toward `rejected`. Does debit count toward `rejected`? If debit did count toward `rejected`, why would it say "and counts toward `rejected`" only for fee? Or does "rejected" in "is rejected and skipped entirely" for debit mean something else?
        # Wait! Let's check if debit counts toward `rejected`.
        # In test_smoke.py:
        # `assert apply(17500, [('fee', 27500), ('fee', 22500), ('debit', 2500)]) == (15000, 2)`
        # Here, opening = 17500.
        # 1. `('fee', 27500)`: 17500 - 27500 = -10000 < 0 -> rejected (rejected = 1).
        # 2. `('fee', 22500)`: 17500 - 22500 = -5000 < 0 -> rejected (rejected = 2).
        # 3. `('debit', 2500)`: 17500 - 2500 = 15000 >= 0 -> allowed. balance = 15000.
        # Result: `(15000, 2)`.
        # What if the third txn was a debit that failed? e.g. `[('debit', 20000)]` on `17500`.
        # Would it be rejected and skipped? Yes. Does it count toward `rejected`?
        pass

if __name__ == '__main__':
    unittest.main()
