import unittest
from intervals import merge, covered


class TestIntervals(unittest.TestCase):
    def test_merge_basic(self):
        self.assertEqual(merge([(1, 3), (2, 6)]), [(1, 6)])

    def test_merge_touching(self):
        self.assertEqual(merge([(1, 3), (3, 5)]), [(1, 5)])

    def test_merge_unsorted(self):
        self.assertEqual(merge([(5, 7), (1, 3), (2, 4)]), [(1, 4), (5, 7)])

    def test_covered(self):
        self.assertEqual(covered([(1, 3), (3, 5)]), 4)
        self.assertEqual(covered([(1, 2), (2, 4), (5, 7)]), 5)


if __name__ == "__main__":
    unittest.main()
