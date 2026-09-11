import unittest
from intervals import merge, covered


class TestIntervals(unittest.TestCase):
    def test_merge_basic(self):
        self.assertEqual(merge([(20, 28)]), [(20, 28)])
        self.assertEqual(merge([(0, 2), (0, 10), (16, 24)]), [(0, 10), (16, 24)])

    def test_merge_touching_intervals(self):
        # Touching intervals (1, 3) and (3, 5) must be separate.
        self.assertEqual(merge([(1, 3), (3, 5)]), [(1, 3), (3, 5)])
        self.assertEqual(merge([(3, 5), (1, 3)]), [(1, 3), (3, 5)])

    def test_merge_overlapping_intervals(self):
        # Overlapping by non-zero amount
        self.assertEqual(merge([(1, 4), (2, 5)]), [(1, 5)])

    def test_merge_sorting(self):
        self.assertEqual(merge([(5, 10), (1, 3)]), [(1, 3), (5, 10)])

    def test_covered_basic(self):
        self.assertEqual(covered([(0, 2), (4, 10)]), 8)

    def test_covered_overlapping(self):
        self.assertEqual(covered([(0, 3), (2, 5)]), 5)  # (0, 5) has length 5

    def test_covered_touching(self):
        self.assertEqual(covered([(1, 3), (3, 5)]), 4)  # (1,3) len 2 + (3,5) len 2 = 4

    def test_covered_nested(self):
        self.assertEqual(covered([(0, 10), (2, 5)]), 10)


if __name__ == "__main__":
    unittest.main()
