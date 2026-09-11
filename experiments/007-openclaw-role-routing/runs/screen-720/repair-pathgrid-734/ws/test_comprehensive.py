import unittest
from pathgrid import steps

class TestPathGrid(unittest.TestCase):
    def test_same_start_goal(self):
        self.assertEqual(steps(['..', '..'], (0, 0), (0, 0)), 0)
        self.assertEqual(steps(['..', '..'], (2, 1), (2, 1)), -1) # out of bounds / wall check

    def test_simple_path(self):
        grid = [
            "...",
            ".X.",
            "..."
        ]
        self.assertEqual(steps(grid, (0, 0), (0, 2)), 2)
        self.assertEqual(steps(grid, (0, 0), (2, 2)), 4)

    def test_unreachable(self):
        grid = [
            "X",
            "X"
        ]
        self.assertEqual(steps(grid, (0, 0), (1, 0)), -1)

if __name__ == "__main__":
    unittest.main()
