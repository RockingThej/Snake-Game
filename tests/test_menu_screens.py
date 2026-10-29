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


if __name__ == "__main__":
    unittest.main()
