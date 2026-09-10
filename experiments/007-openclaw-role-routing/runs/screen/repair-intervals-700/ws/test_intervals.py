import unittest
from intervals import merge, covered


class TestIntervals(unittest.TestCase):
    def test_merge_basic(self):
        self.assertEqual(merge([(1, 3), (3, 5)]), [(1, 5)])

    def test_merge_sort_by_end(self):
        # If sorted by end: (1, 5) and (2, 4) -> (1, 5) absorbs (2, 4) if start <= prev_end, but what about sorting by start?
        # Sorting by start is standard for interval merging.
        self.assertEqual(merge([(2, 4), (1, 5)]), [(1, 5)])

    def test_touching(self):
        self.assertEqual(merge([(1, 3), (3, 5)]), [(1, 5)])

    def test_covered(self):
        self.assertEqual(covered([(1, 3), (3, 5)]), 4)


if __name__ == "__main__":
    unittest.main()
