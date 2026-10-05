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

    def test_cooldown_boundary_exact_is_open(self):
        engine = Engine(1000, 100, 10, 500)
        engine.enqueue("a", 1000, 0)
        engine.enqueue("b", 1000, 0)
        engine.fill(0)
        self.assertFalse(engine.cooldown_ok("a", "b", 999))
        self.assertTrue(engine.cooldown_ok("a", "b", 1000))

    def test_cooldown_allows_rematch_after_window(self):
        engine = Engine(1000, 10000, 10, 500)
        engine.enqueue("a", 1000, 0)
        engine.enqueue("b", 1000, 0)
        engine.fill(0)
        engine.enqueue("a", 1000, 5000)
        engine.enqueue("b", 1000, 5000)
        self.assertEqual(len(engine.fill(5000)), 1)
        self.assertEqual(engine.waiting(), 0)

    def test_rating_gap_over_limit_blocks_pair(self):
        engine = Engine(1000, 100, 10, 500)
        engine.enqueue("a", 1000, 0)
        engine.enqueue("b", 2000, 0)
        self.assertEqual(engine.fill(0), [])
        self.assertEqual(engine.waiting(), 2)

    def test_rating_gap_at_limit_pairs(self):
        engine = Engine(1000, 100, 10, 500)
        engine.enqueue("a", 1000, 0)
        engine.enqueue("b", 1100, 0)
        self.assertEqual(len(engine.fill(0)), 1)

    def test_budget_defers_extra_pairs(self):
        engine = Engine(1000, 10000, 1, 500)
        for player in ("a", "b", "c", "d"):
            engine.enqueue(player, 1000, 0)
        self.assertEqual(len(engine.fill(0)), 1)
        self.assertEqual(engine.deferred, 1)
        self.assertEqual(engine.waiting(), 2)
        self.assertEqual(len(engine.fill(0)), 1)
        self.assertEqual(engine.waiting(), 0)

    def test_undo_within_window_clears_cooldown(self):
        engine = Engine(1000, 10000, 10, 500)
        engine.enqueue("a", 1000, 0)
        engine.enqueue("b", 1000, 0)
        match_id = engine.fill(0)[0][0]
        self.assertTrue(engine.undo(match_id, 100))
        self.assertTrue(engine.cooldown_ok("a", "b", 100))

    def test_undo_at_window_edge_is_accepted(self):
        engine = Engine(1000, 10000, 10, 500)
        engine.enqueue("a", 1000, 0)
        engine.enqueue("b", 1000, 0)
        match_id = engine.fill(0)[0][0]
        self.assertTrue(engine.undo(match_id, 500))

    def test_undo_after_window_fails_and_keeps_cooldown(self):
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
        self.assertFalse(engine.undo("no-such-match", 100))

    def test_duplicate_enqueue_keeps_earliest(self):
        engine = Engine(1000, 100, 10, 500)
        self.assertTrue(engine.enqueue("a", 1000, 0))
        self.assertFalse(engine.enqueue("a", 1000, 10))
        self.assertEqual(engine.waiting(), 1)

    def test_matched_players_leave_queue(self):
        engine = Engine(1000, 100, 10, 500)
        engine.enqueue("a", 1000, 0)
        engine.enqueue("b", 1000, 0)
        engine.fill(0)
        self.assertEqual(engine.waiting(), 0)

    def test_work_not_scaled_by_history(self):
        engine = Engine(1000, 10000, 1000000, 500)
        for index in range(3000):
            engine.enqueue("p-%d" % index, 1000, 0)
        engine.fill(0)
        self.assertLessEqual(engine.work_count(), 6000)


if __name__ == "__main__":
    unittest.main()
