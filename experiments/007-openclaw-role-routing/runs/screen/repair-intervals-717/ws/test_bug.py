import unittest
from intervals import merge, covered


class TestIntervalsBug(unittest.TestCase):
    def test_covered_formula(self):
        # Closed intervals: [start, end] inclusive of endpoints.
        # Length of interval (1, 3) is 1, 2, 3 -> 3 - 1 + 1 = 3.
        # Current covered implementation: `sum(end - start + 1 for start, end in merge(spans))`
        # Wait, what if spans are not normalized or end < start?
        pass

if __name__ == "__main__":
    unittest.main()
