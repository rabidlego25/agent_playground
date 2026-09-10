import unittest
from pathgrid import steps


class TestPathGrid(unittest.TestCase):
    def test_basic(self):
        grid = [
            "...",
            ".#.",
            "..."
        ]
        # (0,0) -> (0,2) -> (1,2) -> (2,2) = 4 steps? Wait:
        # (0,0) -> (0,1) -> (0,2) is 2 steps.
        # But let's check around the wall at (1,1).
        self.assertEqual(steps(grid, (0, 0), (2, 2)), 4)

    def test_start_equals_goal(self):
        self.assertEqual(steps(["..."], (0, 0), (0, 0)), 0)

    def test_start_on_wall(self):
        self.assertEqual(steps(["#."], (0, 0), (0, 1)), -1)

    def test_goal_on_wall(self):
        self.assertEqual(steps([".#"], (0, 0), (0, 1)), -1)

    def test_unreachable(self):
        self.assertEqual(steps([".#."], (0, 0), (0, 2)), -1)

    def test_four_directional_only(self):
        # Diagonal movement should not be allowed
        grid = [
            ".#",
            "#."
        ]
        self.assertEqual(steps(grid, (0, 0), (1, 1)), -1)


if __name__ == "__main__":
    unittest.main()
