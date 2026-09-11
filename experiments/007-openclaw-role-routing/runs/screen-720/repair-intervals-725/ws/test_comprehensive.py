import unittest
from intervals import merge, covered


class TestIntervals(unittest.TestCase):
    def test_touching_intervals(self):
        # Touching intervals (1, 3) and (3, 5) should be separate
        self.assertEqual(merge([(1, 3), (3, 5)]), [(1, 3), (3, 5)])

    def test_overlapping_intervals(self):
        # Overlapping intervals (1, 4) and (3, 5) should merge to (1, 5)
        self.assertEqual(merge([(1, 4), (3, 5)]), [(1, 5)])

    def test_sorting(self):
        self.assertEqual(merge([(5, 7), (1, 3)]), [(1, 3), (5, 7)])

    def test_covered(self):
        self.assertEqual(covered([(1, 3), (3, 5)]), 4)  # (3-1) + (5-3) = 2 + 2 = 4
        self.assertEqual(covered([(1, 4), (3, 5)]), 4)  # length of (1, 5) is 4


if __name__ == "__main__":
    unittest.main()
