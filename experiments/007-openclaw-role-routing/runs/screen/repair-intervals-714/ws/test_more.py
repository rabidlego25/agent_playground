import unittest
from intervals import merge, covered

class TestIntervals(unittest.TestCase):
    def test_merge_touching(self):
        # touching intervals: (1, 3) and (3, 5) -> (1, 5)
        self.assertEqual(merge([(1, 3), (3, 5)]), [(1, 5)])

    def test_merge_overlapping(self):
        self.assertEqual(merge([(1, 4), (2, 5)]), [(1, 5)])

    def test_merge_contained(self):
        self.assertEqual(merge([(1, 5), (2, 3)]), [(1, 5)])

    def test_merge_sorting_and_multiple(self):
        self.assertEqual(
            merge([(30, 35), (40, 45), (15, 25)]),
            [(15, 25), (30, 35), (40, 45)]
        )
        self.assertEqual(
            merge([(30, 40), (45, 55), (0, 5), (0, 15), (5, 25)]),
            [(0, 25), (30, 40), (45, 55)]
        )

    def test_covered(self):
        self.assertEqual(covered([(55, 60), (40, 45)]), 10)
        self.assertEqual(covered([(1, 3), (3, 5)]), 4)
        self.assertEqual(covered([(1, 5), (2, 6)]), 5)

if __name__ == "__main__":
    unittest.main()
