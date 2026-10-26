"""Tests for difficulty speed selection (TC-DIFF-001)."""
import unittest

from engine.game_state import GameState, Status
from modes.difficulty import DifficultyManager


class TestDifficultyManager(unittest.TestCase):
    def setUp(self):
        self.manager = DifficultyManager()

    def test_difficulties_map_to_distinct_movement_speeds(self):
        self.assertEqual(self.manager.get_speed_ms("easy"), 160)
        self.assertEqual(self.manager.get_speed_ms("medium"), 110)
        self.assertEqual(self.manager.get_speed_ms("hard"), 75)

    def test_difficulty_names_are_case_and_whitespace_insensitive(self):
        self.assertEqual(self.manager.get_speed_ms("  HARD "), 75)

    def test_unknown_difficulty_is_rejected(self):
        with self.assertRaises(ValueError):
            self.manager.get_speed_ms("expert")

    def test_custom_speed_values_can_be_supplied(self):
        manager = DifficultyManager({"easy": 200, "hard": 60})
        self.assertEqual(manager.get_speed_ms("easy"), 200)
        self.assertEqual(manager.get_speed_ms("medium"), 110)
        self.assertEqual(manager.get_speed_ms("hard"), 60)

    def test_invalid_custom_speed_values_are_rejected(self):
        for invalid_speed in (0, -10, 1.5, True):
            with self.subTest(speed=invalid_speed):
                with self.assertRaises(ValueError):
                    DifficultyManager({"easy": invalid_speed})


class TestGameDifficulty(unittest.TestCase):
    def test_game_session_uses_selected_difficulty_speed(self):
        state = GameState(difficulty="hard")

        self.assertEqual(state.difficulty, "hard")
        self.assertEqual(state.tick_interval_ms, 75)

    def test_session_uses_injected_difficulty_manager(self):
        manager = DifficultyManager({"hard": 60})
        state = GameState(difficulty="hard", difficulty_manager=manager)

        self.assertEqual(state.tick_interval_ms, 60)

    def test_difficulty_can_change_before_start_and_applies_to_session(self):
        state = GameState(difficulty="easy")
        state.set_difficulty("medium")
        state.start()

        self.assertEqual(state.difficulty, "medium")
        self.assertEqual(state.tick_interval_ms, 110)
        self.assertEqual(state.status, Status.RUNNING)

    def test_difficulty_cannot_change_after_game_starts(self):
        state = GameState()
        state.start()

        with self.assertRaises(RuntimeError):
            state.set_difficulty("hard")

    def test_invalid_difficulty_cannot_be_used_for_a_session(self):
        with self.assertRaises(ValueError):
            GameState(difficulty="expert")


if __name__ == "__main__":
    unittest.main()
