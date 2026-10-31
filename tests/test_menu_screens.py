"""Tests for the main menu, mode selection, difficulty selection, and game-over screens."""
import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

try:
    import pygame  # noqa: E402
except ImportError:  # pragma: no cover - optional runtime dependency
    pygame = None

from engine.game_state import GameState  # noqa: E402
from modes import GameModeManager  # noqa: E402
from ui.menu_screens import (  # noqa: E402
    BattleResultsScreen,
    DifficultySelectionScreen,
    GameOverScreen,
    MainMenuScreen,
    ModeSelectionScreen,
)
from ui.screen_manager import ScreenManager  # noqa: E402


def key(code):
    return pygame.event.Event(pygame.KEYDOWN, key=code)


@unittest.skipIf(pygame is None, "pygame not installed")
class TestMenuScreens(unittest.TestCase):
    def test_main_menu_starts_mode_selection(self):
        manager = ScreenManager()
        menu = MainMenuScreen()
        manager.push(menu)

        menu.handle_event(key(pygame.K_1))

        self.assertIsInstance(manager.current, ModeSelectionScreen)

    def test_mode_screen_lists_registered_modes(self):
        manager = GameModeManager()
        screen = ModeSelectionScreen(mode_manager=manager)

        self.assertIn("Classic", screen.mode_text())
        self.assertIn("coming soon", screen.mode_text().lower())

    def test_difficulty_selection_updates_state(self):
        state = GameState(width=10, height=10)
        screen = DifficultySelectionScreen(state)

        screen.handle_event(key(pygame.K_3))

        self.assertEqual(state.difficulty, "hard")

    def test_game_over_screen_shows_final_score(self):
        state = GameState(width=10, height=10)
        state.score = 42
        screen = GameOverScreen(state)

        self.assertIn("42", screen.score_text())

    def test_battle_results_show_both_scores_and_winner(self):
        state = GameModeManager().create_game("two_player_battle")
        state.scores.update({"player1": 40, "player2": 20})
        state.winner = "player1"
        screen = BattleResultsScreen(state)

        self.assertIn("Player 1: 40", screen.scores_text())
        self.assertIn("Player 2: 20", screen.scores_text())
        self.assertEqual(screen.winner_text(), "Player 1 wins")

    def test_battle_results_report_draw(self):
        state = GameModeManager().create_game("two_player_battle")
        screen = BattleResultsScreen(state)

        self.assertEqual(screen.winner_text(), "Draw")

    def test_battle_results_save_and_show_confirmation(self):
        class SaveManager:
            def save_battle_result(self, state):
                return {"player1": 101, "player2": 102}

        state = GameModeManager().create_game("two_player_battle")
        screen = BattleResultsScreen(state, score_manager=SaveManager())

        screen.on_enter()

        self.assertEqual(state.result_score_ids,
                         {"player1": 101, "player2": 102})
        self.assertIn("saved", screen.save_message.lower())


if __name__ == "__main__":
    unittest.main()
