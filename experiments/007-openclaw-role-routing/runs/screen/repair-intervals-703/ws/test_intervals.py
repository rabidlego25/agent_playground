import unittest
from intervals import merge, covered


class TestIntervals(unittest.TestCase):
    def test_merge_basic(self):
        self.assertEqual(merge([(10, 14), (26, 28)]), [(10, 14), (26, 28)])

    def test_merge_touching(self):
        # Touching intervals ((1, 3) and (3, 5)) must remain separate
        self.assertEqual(merge([(1, 3), (3, 5)]), [(1, 3), (3, 5)])

    def test_merge_overlapping(self):
        self.assertEqual(merge([(1, 3), (2, 4)]), [(1, 4)])

    def test_merge_unsorted(self):
        self.assertEqual(merge([(5, 10), (1, 3)]), [(1, 3), (5, 10)])

    def test_covered_basic(self):
        self.assertEqual(covered([(10, 12), (20, 26)]), 8)

    def test_covered_overlapping(self):
        self.assertEqual(covered([(1, 3), (2, 4)]), 3)

    def test_covered_touching(self):
        self.assertEqual(covered([(1, 3), (3, 5)]), 4)


if __name__ == "__main__":
    unittest.main()
