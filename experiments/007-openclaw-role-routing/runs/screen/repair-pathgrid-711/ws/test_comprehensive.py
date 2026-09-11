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
        grid = [
            "..."
        ]
        self.assertEqual(steps(grid, (0, 0), (0, 0)), 0)
        self.assertEqual(steps(grid, (0, 1), (0, 1)), 0)

    def test_wall_start_goal(self):
        grid = [
            "X."
        ]
        self.assertEqual(steps(grid, (0, 0), (0, 1)), -1)
        self.assertEqual(steps(grid, (0, 1), (0, 0)), -1)

    def test_unreachable(self):
        grid = [
            ".X.",
            "X.X",
            ".X."
        ]
        self.assertEqual(steps(grid, (0, 0), (2, 2)), -1)

    def test_bounds(self):
        grid = ["...."]
        # r=0, c=4 would be out of bounds, let's verify open_cell boundary check
        # With `0 <= r <= rows and 0 <= c <= cols`, r=0, c=4 is considered valid by open_cell!
        # Let's test accessing grid[0][4] which raises IndexError or accesses out of bounds.
        # But wait, does our test trigger out of bounds or invalid indexing?
        # Let's check what happens when we query a point outside grid using steps or directly calling open_cell via steps.
        # Actually, let's test steps with start or goal or neighbor out of bounds.
        self.assertEqual(steps(grid, (0, 0), (0, 5)), -1)

if __name__ == '__main__':
    unittest.main()
