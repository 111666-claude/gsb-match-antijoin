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

    def test_cooldown_exactly_at_boundary_is_open(self):
        engine = Engine(1000, 100, 10, 500)
        engine.enqueue("a", 1000, 0)
        engine.enqueue("b", 1000, 0)
        engine.fill(0)
        self.assertFalse(engine.cooldown_ok("b", "a", 999))
        self.assertTrue(engine.cooldown_ok("a", "b", 1000))

    def test_repair_after_cooldown_succeeds(self):
        engine = Engine(1000, 10000, 10, 500)
        engine.enqueue("a", 1000, 0)
        engine.enqueue("b", 1000, 0)
        self.assertEqual(len(engine.fill(0)), 1)
        engine.enqueue("a", 1000, 5000)
        engine.enqueue("b", 1000, 5000)
        again = engine.fill(5000)
        self.assertEqual(len(again), 1)
        self.assertEqual(engine.waiting(), 0)

    def test_rating_gap_over_max_blocks_pair(self):
        engine = Engine(1000, 100, 10, 500)
        engine.enqueue("a", 1000, 0)
        engine.enqueue("b", 2000, 0)
        self.assertEqual(engine.fill(0), [])
        self.assertEqual(engine.waiting(), 2)

    def test_rating_gap_at_boundary_pairs(self):
        engine = Engine(1000, 100, 10, 500)
        engine.enqueue("a", 1000, 0)
        engine.enqueue("b", 1100, 0)
        self.assertEqual(len(engine.fill(0)), 1)

    def test_budget_defers_extra_pairs(self):
        engine = Engine(1000, 10000, 1, 500)
        for name in "abcd":
            engine.enqueue(name, 1000, 0)
        made = engine.fill(0)
        self.assertEqual(len(made), 1)
        self.assertEqual(engine.deferred, 1)
        self.assertEqual(engine.waiting(), 2)

    def test_deferred_players_can_fill_later(self):
        engine = Engine(1000, 10000, 1, 500)
        for name in "abcd":
            engine.enqueue(name, 1000, 0)
        engine.fill(0)
        self.assertEqual(len(engine.fill(10)), 1)
        self.assertEqual(engine.waiting(), 0)

    def test_undo_within_window_clears_cooldown(self):
        engine = Engine(1000, 10000, 10, 500)
        engine.enqueue("a", 1000, 0)
        engine.enqueue("b", 1000, 0)
        match_id = engine.fill(0)[0][0]
        self.assertTrue(engine.undo(match_id, 100))
        self.assertTrue(engine.cooldown_ok("a", "b", 100))
        engine.enqueue("a", 1000, 100)
        engine.enqueue("b", 1000, 100)
        self.assertEqual(len(engine.fill(100)), 1)

    def test_undo_after_window_returns_false_and_keeps_cooldown(self):
        engine = Engine(1000, 10000, 10, 500)
        engine.enqueue("a", 1000, 0)
        engine.enqueue("b", 1000, 0)
        match_id = engine.fill(0)[0][0]
        self.assertFalse(engine.undo(match_id, 501))
        self.assertFalse(engine.cooldown_ok("a", "b", 501))

    def test_undo_is_idempotent(self):
        engine = Engine(1000, 10000, 10, 500)
        engine.enqueue("a", 1000, 0)
        engine.enqueue("b", 1000, 0)
        match_id = engine.fill(0)[0][0]
        self.assertTrue(engine.undo(match_id, 100))
        self.assertFalse(engine.undo(match_id, 100))

    def test_duplicate_enqueue_keeps_earliest(self):
        engine = Engine(1000, 100, 10, 500)
        self.assertTrue(engine.enqueue("a", 1000, 0))
        self.assertFalse(engine.enqueue("a", 9999, 10))
        self.assertEqual(engine.waiting(), 1)
        engine.enqueue("b", 2000, 0)
        self.assertEqual(engine.fill(0), [])

    def test_work_does_not_scale_with_history(self):
        first = Engine(1000, 10000, 1000000, 500)
        for index in range(100):
            first.enqueue("p-%d" % index, 1000, 0)
        first.fill(0)
        second = Engine(1000, 10000, 1000000, 500)
        for index in range(3000):
            second.enqueue("p-%d" % index, 1000, 0)
        second.fill(0)
        self.assertLessEqual(second.work_count(), first.work_count() * 30)


if __name__ == "__main__":
    unittest.main()
