import unittest
from ledger import apply

class LedgerTest(unittest.TestCase):
    def test_spec(self):
        # Let's write unit tests covering all aspects of the specification:
        # 1. FLOOR = -2000
        # 2. Debit uses current balance, checks < -2000, and does it increment rejected?
        # Wait, let's re-read:
        # "A debit that would take the balance below the overdraft floor of -2000 cents is rejected and skipped entirely. A fee that would take the balance past the floor is rejected and skipped too, and counts toward `rejected`."
        # Wait, does debit count toward `rejected`?
        # Let's parse sentence structure:
        # "A debit that would take the balance below the overdraft floor of -2000 cents is rejected and skipped entirely." -> does it increment rejected?
        # "A fee that would take the balance past the floor is rejected and skipped too, and counts toward `rejected`." -> explicitly mentions counts toward rejected. Wait, why would fee mention "counts toward `rejected`"? Does debit NOT count toward rejected, or does rejected count all skipped transactions?
        # Wait, let's re-read the paragraph:
        # "`apply(opening, txns)` processes each `(kind, amount)` in order. `kind` is `"credit"`, `"debit"` or `"fee"`. A debit that would take the balance below the overdraft floor of -2000 cents is rejected and skipped entirely. A fee that would take the balance past the floor is rejected and skipped too, and counts toward `rejected`. `apply` returns `(balance, rejected)` where `rejected` is the count of skipped transactions."
        # "where `rejected` is the count of skipped transactions."
        # If `rejected` is the count of skipped transactions, then any skipped transaction (whether debit or fee) increments `rejected`! Why did the sentence say "and counts toward `rejected`" for fee? Because people often specify features or clarify. But wait, let's check if debit increments rejected or not.
        # Wait, "A debit that would take the balance below the overdraft floor of -2000 cents is rejected and skipped entirely." -> rejected means it is rejected (i.e. skipped, count towards rejected).
        pass

if __name__ == '__main__':
    unittest.main()
