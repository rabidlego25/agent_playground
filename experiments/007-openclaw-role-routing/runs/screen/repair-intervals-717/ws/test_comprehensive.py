import unittest
from intervals import merge, covered


class TestIntervals(unittest.TestCase):
    def test_merge_touching(self):
        self.assertEqual(merge([(1, 3), (3, 5)]), [(1, 5)])
        self.assertEqual(merge([(3, 5), (1, 3)]), [(1, 5)])

    def test_covered_calculation(self):
        # Let's test various cases
        self.assertEqual(covered([(1, 3)]), 3)
        self.assertEqual(covered([(1, 3), (3, 5)]), 5)
        self.assertEqual(covered([(1, 2), (4, 5)]), 4)

    def test_edge_cases(self):
        self.assertEqual(merge([]), [])
        self.assertEqual(covered([]), 0)
        self.assertEqual(merge([(5, 2)]), [(2, 5)])  # what if start > end? or negative?

if __name__ == "__main__":
    unittest.main()
