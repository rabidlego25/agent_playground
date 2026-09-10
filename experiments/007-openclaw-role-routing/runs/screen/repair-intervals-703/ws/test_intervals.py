import unittest
from intervals import merge, covered


class IntervalTests(unittest.TestCase):

    def test_merge_basic(self):
        self.assertEqual(merge([(10, 14), (26, 28)]), [(10, 14), (26, 28)])

    def test_merge_touching(self):
        # Touching intervals ((1, 3) and (3, 5)) must NOT be combined because they are separate.
        self.assertEqual(merge([(1, 3), (3, 5)]), [(1, 3), (3, 5)])

    def test_merge_overlapping(self):
        self.assertEqual(merge([(1, 4), (2, 5)]), [(1, 5)])

    def test_merge_unsorted(self):
        self.assertEqual(merge([(3, 5), (1, 3)]), [(1, 3), (3, 5)])
        self.assertEqual(merge([(5, 6), (1, 3)]), [(1, 3), (5, 6)])

    def test_merge_subsumed(self):
        self.assertEqual(merge([(1, 5), (2, 4)]), [(1, 5)])

    def test_covered(self):
        self.assertEqual(covered([(10, 12), (20, 26)]), 8)
        self.assertEqual(covered([(1, 3), (3, 5)]), 4)  # (3-1) + (5-3) = 2 + 2 = 4
        self.assertEqual(covered([(1, 4), (2, 5)]), 4)  # merged to (1, 5) -> length 4


if __name__ == "__main__":
    unittest.main()
