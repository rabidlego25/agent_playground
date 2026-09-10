import unittest
from pathgrid import steps

class TestPathGrid(unittest.TestCase):
    def test_start_equals_goal(self):
        self.assertEqual(steps(['..', '..'], (0, 0), (0, 0)), 0)
        self.assertEqual(steps(['..', '.X'], (1, 1), (1, 1)), -1)

    def test_unreachable(self):
        self.assertEqual(steps(['.X', 'X.'], (0, 0), (1, 1)), -1)

    def test_diagonal(self):
        self.assertEqual(steps(['...', '...', '...'], (0, 0), (2, 2)), 2)

    def test_obstacle(self):
        self.assertEqual(steps(['...', '.X.', '...'], (0, 0), (2, 2)), 2)

if __name__ == '__main__':
    unittest.main()
