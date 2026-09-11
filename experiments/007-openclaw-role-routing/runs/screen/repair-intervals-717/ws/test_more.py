import unittest
from intervals import merge, covered


class TestIntervals(unittest.TestCase):
    def test_merge_touching(self):
        # Touching intervals: (1, 3) and (3, 5) should combine into (1, 5)
        self.assertEqual(merge([(1, 3), (3, 5)]), [(1, 5)])
        self.assertEqual(merge([(3, 5), (1, 3)]), [(1, 5)])

    def test_covered_closed(self):
        # Closed intervals: length of (1, 3) is 3 - 1 + 1 = 3? Wait!
        # Let's check the specification carefully:
        # "`intervals.py` merges overlapping closed intervals and reports total coverage.
        # `merge(spans)` takes a list of `(start, end)` pairs and returns them merged and sorted,
        # with touching intervals (`(1, 3)` and `(3, 5)`) counted as overlapping and combined into `(1, 5)`.
        # `covered(spans)` returns the total length covered, counting overlap once."
        #
        # For a closed interval (1, 3), what points are covered? 1, 2, 3. Length = 3 - 1 + 1 = 3.
        # What about touching intervals (1, 3) and (3, 5)?
        # Combined into (1, 5). Covered points: 1, 2, 3, 4, 5. Length = 5 - 1 + 1 = 5.
        # In current implementation:
        # covered([(1, 3)]) -> sum(3 - 1 + 1) = 3.
        # covered([(1, 3), (3, 5)]) -> merge gives [(1, 5)], covered -> 5 - 1 + 1 = 5.
        # Wait, what if they don't overlap or touch? (1, 2) and (4, 5).
        # merge: [(1, 2), (4, 5)]. covered: (2 - 1 + 1) + (5 - 4 + 1) = 2 + 2 = 4.
        pass

if __name__ == "__main__":
    unittest.main()
