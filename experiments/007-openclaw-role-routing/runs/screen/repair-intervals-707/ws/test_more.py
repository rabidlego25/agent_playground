import unittest
from intervals import merge, covered


class TestIntervals(unittest.TestCase):
    def test_merge_touching(self):
        # touching intervals (1, 3) and (3, 5) should remain separate
        self.assertEqual(merge([(1, 3), (3, 5)]), [(1, 3), (3, 5)])

    def test_merge_overlapping(self):
        # overlapping intervals (1, 3) and (2, 4) should merge to (1, 4)
        self.assertEqual(merge([(1, 3), (2, 4)]), [(1, 4)])

    def test_merge_contained(self):
        self.assertEqual(merge([(1, 5), (2, 3)]), [(1, 5)])

    def test_covered(self):
        self.assertEqual(covered([(1, 3), (3, 5)]), 4)  # 2 + 2


if __name__ == "__main__":
    unittest.main()
