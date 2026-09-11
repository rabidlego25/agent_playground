import unittest
from intervals import merge, covered


class TestIntervals(unittest.TestCase):
    def test_merge_basic(self):
        self.assertEqual(
            merge([(1, 3), (2, 4), (5, 7)]),
            [(1, 4), (5, 7)]
        )

    def test_merge_touching_separate(self):
        # Touch at 3: (1, 3) and (3, 5) should remain separate
        self.assertEqual(
            merge([(1, 3), (3, 5)]),
            [(1, 3), (3, 5)]
        )

    def test_merge_unsorted(self):
        self.assertEqual(
            merge([(5, 7), (1, 3), (2, 4)]),
            [(1, 4), (5, 7)]
        )

    def test_merge_subset(self):
        self.assertEqual(
            merge([(1, 5), (2, 3)]),
            [(1, 5)]
        )

    def test_covered_basic(self):
        self.assertEqual(
            covered([(1, 3), (2, 4)]),
            3  # [1, 4] length is 3
        )

    def test_covered_touching(self):
        self.assertEqual(
            covered([(1, 3), (3, 5)]),
            4  # (3 - 1) + (5 - 3) = 2 + 2 = 4
        )

    def test_covered_overlapping(self):
        self.assertEqual(
            covered([(1, 4), (2, 5)]),
            4  # [1, 5] length is 4
        )


if __name__ == "__main__":
    unittest.main()
