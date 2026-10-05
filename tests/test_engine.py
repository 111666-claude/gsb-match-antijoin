import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from antijoin.engine import Engine  # noqa: E402


class EngineTest(unittest.TestCase):
    def test_fresh_pair_is_allowed(self):
        engine = Engine(1000, 100, 10, 500)
        self.assertTrue(engine.cooldown_ok("a", "b", 0))

    def test_pair_inside_cooldown_is_blocked(self):
        engine = Engine(1000, 100, 10, 500)
        engine.enqueue("a", 1000, 0)
        engine.enqueue("b", 1000, 0)
        engine.fill(0)
        self.assertFalse(engine.cooldown_ok("a", "b", 500))

    def test_waiting_counts_queue(self):
        engine = Engine(1000, 100, 10, 500)
        engine.enqueue("a", 1000, 0)
        self.assertEqual(engine.waiting(), 1)

    def test_work_starts_at_zero(self):
        self.assertEqual(Engine(1000, 100, 10, 500).work_count(), 0)


if __name__ == "__main__":
    unittest.main()
