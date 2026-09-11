import unittest
from intervals import merge, covered


class TestIntervals(unittest.TestCase):
    def test_merge_sorting_and_touching(self):
        # Unsorted input, touching intervals
        self.assertEqual(merge([(3, 5), (1, 3)]), [(1, 5)])
        self.assertEqual(merge([(1, 3), (3, 5)]), [(1, 5)])
        self.assertEqual(merge([(5, 7), (1, 3), (2, 6)]), [(1, 7)])

    def test_covered(self):
        # Overlapping and touching intervals
        self.assertEqual(covered([(1, 3), (3, 5)]), 4)
        self.assertEqual(covered([(1, 3), (2, 4), (5, 6)]), 4)


if __name__ == "__main__":
    unittest.main()
