import unittest
from intervals import merge, covered


class TestIntervals(unittest.TestCase):
    def test_merge_sorting(self):
        # Unsorted spans should be sorted and merged correctly
        self.assertEqual(merge([(5, 10), (1, 3)]), [(1, 3), (5, 10)])

    def test_merge_touching(self):
        # Touching intervals should combine: (1, 3) and (3, 5) -> (1, 5)
        self.assertEqual(merge([(1, 3), (3, 5)]), [(1, 5)])

    def test_covered_basic(self):
        self.assertEqual(covered([(1, 3), (3, 5)]), 4)


if __name__ == '__main__':
    unittest.main()
