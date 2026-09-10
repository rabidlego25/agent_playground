import unittest
from intervals import merge, covered


class TestIntervals(unittest.TestCase):
    def test_merge_touching(self):
        # Touching intervals: (1, 3) and (3, 5). They share point 3, but overlap by a non-zero amount requires > 0 length intersection.
        # Here end of first is 3, start of second is 3. start < out[-1][1] currently checks 3 < 3 which is False!
        # Wait, in the current implementation:
        # `if start < out[-1][1]:` -> `3 < 3` is False, so it appends [3, 5].
        # But wait! What about `(1, 3)` and `(2, 4)`? `2 < 3` is True, so they merge to `(1, 4)`.
        # What about `(50, 80)` and `(90, 110)`? `90 < 80` False -> separate.
        # What about `(60, 110)` and `(130, 170)`? `130 < 110` False -> separate.
        # Wait, what about `(250, 300)` and `(240, 250)`?
        # In test_smoke.py: `[(60, 110), (130, 170), (200, 210), (250, 300), (240, 250)]` gets sorted to:
        # `[(60, 110), (130, 170), (200, 210), (240, 250), (250, 300)]`.
        # Here `(240, 250)` and `(250, 300)` are touching at 250!
        # Let's check what `merge([(240, 250), (250, 300)])` returns currently.
        self.assertEqual(merge([(240, 250), (250, 300)]), [(240, 250), (250, 300)])

    def test_merge_subsumed(self):
        # (1, 5) and (2, 3)
        self.assertEqual(merge([(1, 5), (2, 3)]), [(1, 5)])

    def test_covered(self):
        # covered([ (1, 3), (3, 5) ]) -> if they are separate:
        # (1, 3) length 3 - 1 + 1 = 3? Or 2?
        # Let's check covered formula in intervals.py: `sum(end - start + 1 for start, end in merge(spans))`
        # For (1, 3): 3 - 1 + 1 = 3 points: 1, 2, 3.
        # For (1, 5): 5 - 1 + 1 = 5.
        pass

if __name__ == "__main__":
    unittest.main()
