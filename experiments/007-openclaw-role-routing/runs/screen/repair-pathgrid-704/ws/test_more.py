import unittest
from pathgrid import steps


class TestPathGrid(unittest.TestCase):

    def test_smoke(self):
        self.assertEqual(steps(["...", "...", "..."], (0, 0), (0, 2)), 2)
        self.assertEqual(steps(["...", "...", "..."], (1, 1), (1, 1)), 0)

    def test_four_directional(self):
        # Diagonal movement is incorrectly allowed in the bug version
        grid = [
            ".#.",
            ".#.",
            "...",
        ]
        # From (0,0) to (2,0):
        # 4-directional path: (0,0) -> (1,0) is wall? Wait (1,0) is '#' (wall)
        # Let's design a grid where diagonal is shorter than 4-directional, or diagonal makes it work when 4-directional is blocked or longer.
        grid = [
            ".#.",
            "...",
            "...",
        ]
        # From (0,0) to (0,2):
        # 4-directional: (0,0) -> (1,0) -> (1,1) -> (1,2) -> (0,2) = 4 steps
        # Diagonal: (0,0) -> (1,1) -> (0,2) = 2 steps (if diagonal allowed)
        # Specification: Movement is four-directional.
        # So shortest 4-directional path from (0,0) to (0,2) is length 4.
        self.assertEqual(steps(grid, (0, 0), (0, 2)), 4)


if __name__ == "__main__":
    unittest.main()
