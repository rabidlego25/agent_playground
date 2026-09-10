import unittest
from pathgrid import steps

class TestPathGrid(unittest.TestCase):
    def test_basic(self):
        grid = [
            "...",
            ".@.",
            "..."
        ]
        self.assertEqual(steps(grid, (0, 0), (2, 2)), 4)

    def test_same_start_goal(self):
        grid = [
            "...",
            "..."
        ]
        self.assertEqual(steps(grid, (1, 1), (1, 1)), 0)

    def test_wall_start_goal(self):
        grid = [
            "@.",
            ".."
        ]
        self.assertEqual(steps(grid, (0, 0), (1, 1)), -1)
        self.assertEqual(steps(grid, (1, 1), (0, 0)), -1)

    def test_unreachable(self):
        grid = [
            ".@",
            "@."
        ]
        self.assertEqual(steps(grid, (0, 0), (1, 1)), -1)

if __name__ == "__main__":
    unittest.main()
