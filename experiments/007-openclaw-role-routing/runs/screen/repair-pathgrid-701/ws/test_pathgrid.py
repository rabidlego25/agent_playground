import unittest
from pathgrid import steps

class TestPathGrid(unittest.TestCase):
    def test_basic(self):
        grid = [
            "...",
            ".X.",
            "..."
        ]
        self.assertEqual(steps(grid, (0, 0), (2, 2)), 4)

    def test_start_equals_goal(self):
        grid = ["...", "..."]
        self.assertEqual(steps(grid, (0, 0), (0, 0)), 0)

    def test_start_on_wall(self):
        grid = ["X.", ".."]
        self.assertEqual(steps(grid, (0, 0), (1, 1)), -1)

    def test_goal_on_wall(self):
        grid = [".X", ".."]
        self.assertEqual(steps(grid, (0, 0), (0, 1)), -1)

    def test_unreachable(self):
        grid = [
            ".X.",
            "X.X",
            ".X."
        ]
        self.assertEqual(steps(grid, (0, 0), (2, 2)), -1)

if __name__ == "__main__":
    unittest.main()
