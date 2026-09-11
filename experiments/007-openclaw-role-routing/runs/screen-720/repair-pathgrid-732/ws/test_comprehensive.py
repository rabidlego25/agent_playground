import unittest
from pathgrid import steps

class TestPathGrid(unittest.TestCase):
    def test_same_start_goal(self):
        self.assertEqual(steps(['...'], (0, 0), (0, 0)), 0)
        self.assertEqual(steps(['X'], (0, 0), (0, 0)), -1)

    def test_movement_directions(self):
        # DELTAS only had ((1, 0), (-1, 0), (0, 1)), missing left (0, -1)!
        grid = ['...', '...', '...']
        self.assertEqual(steps(grid, (0, 1), (0, 0)), 1)

    def test_unreachable_returns_minus_one(self):
        grid = ['X..', 'X..']
        self.assertEqual(steps(grid, (1, 1), (0, 0)), -1)

if __name__ == '__main__':
    unittest.main()
