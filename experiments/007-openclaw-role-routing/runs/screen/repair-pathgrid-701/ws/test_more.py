import unittest
from pathgrid import steps

class TestPathGrid(unittest.TestCase):
    def test_basic(self):
        grid = [
            "...",
            ".X.",
            "..."
        ]
        # Start at (0,0), goal at (0,2)
        # Paths could be (0,0)->(0,1)->(0,2) length 2, or down around
        self.assertEqual(steps(grid, (0, 0), (0, 2)), 2)

    def test_same_start_goal(self):
        grid = [
            "..."
        ]
        self.assertEqual(steps(grid, (0, 1), (0, 1)), 0)

    def test_start_on_wall(self):
        grid = [
            "X.."
        ]
        self.assertEqual(steps(grid, (0, 0), (0, 2)), -1)

    def test_goal_on_wall(self):
        grid = [
            "..X"
        ]
        self.assertEqual(steps(grid, (0, 0), (0, 2)), -1)

    def test_unreachable(self):
        grid = [
            ".X.",
            "X.X",
            ".X."
        ]
        self.assertEqual(steps(grid, (0, 0), (2, 2)), -1)

if __name__ == '__main__':
    unittest.main()
