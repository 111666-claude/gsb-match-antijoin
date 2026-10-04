import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from antijoin.engine import Engine  # noqa: E402


class EngineTest(unittest.TestCase):
    def test_fresh_pair_is_allowed(self):
        self.assertTrue(Engine(1000).pair("m1", "a", "b", 0))

    def test_repeat_pair_inside_cooldown_is_blocked(self):
        engine = Engine(1000)
        engine.pair("m1", "a", "b", 0)
        self.assertFalse(engine.pair("m2", "b", "a", 500))

    def test_work_starts_at_zero(self):
        self.assertEqual(Engine(1000).work_count(), 0)


if __name__ == "__main__":
    unittest.main()
