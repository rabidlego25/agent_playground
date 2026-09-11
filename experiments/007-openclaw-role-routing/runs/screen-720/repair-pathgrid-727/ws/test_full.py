import unittest
from pathgrid import steps

class TestPathGrid(unittest.TestCase):
    def test_start_equals_goal(self):
        self.assertEqual(steps(['...'], (0, 0), (0, 0)), 0)

    def test_start_on_wall(self):
        self.assertEqual(steps(['.@.'], (0, 1), (0, 0)), -1)

    def test_goal_on_wall(self):
        self.assertEqual(steps(['.@.'], (0, 0), (0, 1)), -1)

    def test_basic(self):
        self.assertEqual(steps(['....', '....'], (0, 1), (1, 0)), 2)

if __name__ == '__main__':
    unittest.main()
