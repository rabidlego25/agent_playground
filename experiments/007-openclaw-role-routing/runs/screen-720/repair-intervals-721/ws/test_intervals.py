import unittest
from intervals import merge, covered


class TestIntervals(unittest.TestCase):
    def test_merge_basic(self):
        self.assertEqual(merge([(1, 3), (2, 4)]), [(1, 4)])

    def test_merge_touching(self):
        # Touching intervals ((1, 3) and (3, 5)) must remain separate
        self.assertEqual(merge([(1, 3), (3, 5)]), [(1, 3), (3, 5)])

    def test_merge_unsorted(self):
        self.assertEqual(merge([(5, 7), (1, 3), (2, 6)]), [(1, 7)])

    def test_merge_subsumed(self):
        self.assertEqual(merge([(1, 5), (2, 3)]), [(1, 5)])

    def test_merge_empty(self):
        self.assertEqual(merge([]), [])

    def test_covered(self):
        self.assertEqual(covered([(1, 3), (3, 5)]), 4)  # (3-1) + (5-3) = 2 + 2 = 4
        self.assertEqual(covered([(1, 4), (2, 6)]), 5)  # [1, 6] length 5


if __name__ == "__main__":
    unittest.main()
