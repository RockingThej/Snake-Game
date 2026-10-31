"""Tests for the five-mode registry (TC-MODE-001)."""
import unittest

from engine.game_state import GameState
from engine.two_player_game_state import TwoPlayerGameState
from modes import GameModeManager, ModeNotImplementedError


class TestGameModeManager(unittest.TestCase):
    def setUp(self):
        self.manager = GameModeManager()

    def test_all_five_srs_modes_are_registered(self):
        self.assertEqual(
            [mode.id for mode in self.manager.list_modes()],
            [
                "classic",
                "obstacle",
                "power_up",
                "two_player_battle",
                "survival",
            ],
        )

    def test_each_mode_can_be_selected_by_menu_key_and_name(self):
        for mode in self.manager.list_modes():
            with self.subTest(mode=mode.id):
                self.assertEqual(
                    self.manager.select_mode(mode.selection_key), mode
                )
                self.assertEqual(self.manager.select_mode(mode.name), mode)

    def test_classic_mode_creates_game_state(self):
        state = self.manager.create_game(
            "classic", width=12, height=10, difficulty="hard"
        )

        self.assertIsInstance(state, GameState)
        self.assertEqual(state.mode, "classic")
        self.assertEqual(state.difficulty, "hard")

    def test_two_player_battle_creates_two_player_state(self):
        state = self.manager.create_game(
            "two_player_battle", width=18, height=10
        )

        self.assertIsInstance(state, TwoPlayerGameState)
        self.assertEqual(tuple(state.snakes), ("player1", "player2"))
        self.assertEqual(state.scores, {"player1": 0, "player2": 0})

    def test_unimplemented_modes_fail_with_clear_message(self):
        for mode in self.manager.list_modes():
            if mode.implemented:
                continue
            with self.subTest(mode=mode.id):
                with self.assertRaisesRegex(
                    ModeNotImplementedError,
                    rf"{mode.name} Mode is registered but is not implemented yet",
                ):
                    self.manager.create_game(mode.id)

    def test_unknown_mode_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown game mode"):
            self.manager.select_mode("arcade")


if __name__ == "__main__":
    unittest.main()
