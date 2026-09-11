import unittest
from pathgrid import steps

class TestPathGrid(unittest.TestCase):
    def test_same_start_goal(self):
        grid = ['...', '...', '...']
        self.assertEqual(steps(grid, (1, 1), (1, 1)), 0)

    def test_wall_start_goal(self):
        grid = ['#..', '...', '...']
        self.assertEqual(steps(grid, (0, 0), (1, 1)), -1)
        self.assertEqual(steps(grid, (1, 1), (0, 0)), -1)

    def test_four_directions(self):
        grid = ['...', '...', '...']
        # DELTAS in pathgrid.py only has ((1, 0), (-1, 0), (0, 1)) - missing (0, -1)!
        self.assertEqual(steps(grid, (1, 1), (1, 0)), 1)

    def test_unreachable(self):
        grid = ['.#.', '#.#', '.#.']
        self.assertEqual(steps(grid, (0, 0), (2, 2)), -1)

    def test_empty_queue_return(self):
        # If goal unreachable, returns 0 instead of -1 at the end of function!
        grid = ['..#', '..#', '###']
        self.assertEqual(steps(grid, (0, 0), (2, 2)), -1)

if __name__ == '__main__':
    unittest.main()
