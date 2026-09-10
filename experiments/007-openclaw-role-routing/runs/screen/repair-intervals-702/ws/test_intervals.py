import unittest
from intervals import merge, covered


class TestIntervals(unittest.TestCase):
    def test_smoke(self):
        self.assertEqual(merge([(1, 2), (5, 6)]), [(1, 2), (5, 6)])
        self.assertEqual(covered([(1, 2), (5, 6)]), 2)

    def test_touching_intervals(self):
        # Touching intervals: (1, 3) and (3, 5) should combine to (1, 5)
        self.assertEqual(merge([(1, 3), (3, 5)]), [(1, 5)])
        self.assertEqual(covered([(1, 3), (3, 5)]), 4)

    def test_overlapping_intervals(self):
        self.assertEqual(merge([(1, 4), (2, 6)]), [(1, 6)])
        self.assertEqual(covered([(1, 4), (2, 6)]), 5)

    def test_contained_intervals(self):
        self.assertEqual(merge([(1, 5), (2, 3)]), [(1, 5)])
        self.assertEqual(covered([(1, 5), (2, 3)]), 4)

    def test_end_extension(self):
        # Bug check: when a later interval's end is smaller than out[-1][1],
        # e.g., (1, 5) and (2, 3), out[-1][1] should remain 5, not become 3.
        # Let's check with (1, 5) and (2, 4):
        self.assertEqual(merge([(1, 5), (2, 4)]), [(1, 5)])


if __name__ == "__main__":
    unittest.main()
