"""End-to-end flow through main.build_app: register -> play -> game over."""
import os
import shutil
import tempfile
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

try:
    import pygame
    from engine.game_state import Status
    from main import build_app
    from ui.auth_screens import LoginScreen, RegisterScreen
    from ui.game_screen import GameScreen
    from ui.leaderboard_screen import LeaderboardScreen
    from ui.menu_screens import (
        DifficultySelectionScreen,
        GameOverScreen,
        MainMenuScreen,
        ModeSelectionScreen,
    )
except ImportError:  # pygame is not installed
    pygame = None


def key(code, char=""):
    return pygame.event.Event(pygame.KEYDOWN, key=code, unicode=char)


def type_text(screen, text):
    for char in text:
        screen.handle_event(key(ord(char), char))


@unittest.skipIf(pygame is None, "pygame not installed")
class TestLauncherFlow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.manager, first = build_app(os.path.join(self.tmp, "flow.sqlite3"))
        self.manager.replace(first())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def register(self, name="alice1", password="secret123"):
        self.manager.current.handle_event(key(pygame.K_F2))
        screen = self.manager.current
        self.assertIsInstance(screen, RegisterScreen)
        type_text(screen, name)
        screen.handle_event(key(pygame.K_TAB))
        type_text(screen, password)
        screen.handle_event(key(pygame.K_TAB))
        type_text(screen, password)
        screen.handle_event(key(pygame.K_RETURN))

    def test_starts_on_login(self):
        self.assertIsInstance(self.manager.current, LoginScreen)

    def test_register_logs_in_and_opens_menu(self):
        self.register()
        self.assertIsInstance(self.manager.current, MainMenuScreen)
        self.assertEqual(self.manager.session.username, "alice1")

    def test_login_after_logout(self):
        self.register()
        self.manager.current.handle_event(key(pygame.K_3))   # log out
        screen = self.manager.current
        self.assertIsInstance(screen, LoginScreen)
        type_text(screen, "alice1")
        screen.handle_event(key(pygame.K_TAB))
        type_text(screen, "secret123")
        screen.handle_event(key(pygame.K_RETURN))
        self.assertIsInstance(self.manager.current, MainMenuScreen)

    def test_wrong_password_stays_on_login(self):
        self.register()
        self.manager.current.handle_event(key(pygame.K_3))
        screen = self.manager.current
        type_text(screen, "alice1")
        screen.handle_event(key(pygame.K_TAB))
        type_text(screen, "wrongpass")
        screen.handle_event(key(pygame.K_RETURN))
        self.assertIsInstance(self.manager.current, LoginScreen)
        self.assertIn("Invalid", self.manager.current.message)

    def test_full_game_saves_score_and_shows_leaderboard(self):
        self.register()
        self.manager.current.handle_event(key(pygame.K_1))   # Play
        self.assertIsInstance(self.manager.current, ModeSelectionScreen)
        self.manager.current.handle_event(key(pygame.K_1))   # Classic
        self.assertIsInstance(self.manager.current, DifficultySelectionScreen)
        self.manager.current.handle_event(key(pygame.K_2))   # Medium
        game = self.manager.current
        self.assertIsInstance(game, GameScreen)

        game.handle_event(key(pygame.K_RIGHT))     # start, run into the wall
        game.update(10.0)

        self.assertEqual(game.state.status, Status.GAME_OVER)
        over = self.manager.current
        self.assertIsInstance(over, GameOverScreen)
        self.assertTrue(over.saved)

        over.handle_event(key(pygame.K_l))
        board = self.manager.current
        self.assertIsInstance(board, LeaderboardScreen)
        self.assertEqual(board.entries[0]["username"], "alice1")

    def test_escape_in_game_returns_to_menu(self):
        self.register()
        self.manager.current.handle_event(key(pygame.K_1))
        self.manager.current.handle_event(key(pygame.K_1))
        self.manager.current.handle_event(key(pygame.K_2))
        self.manager.current.handle_event(key(pygame.K_ESCAPE))
        self.assertIsInstance(self.manager.current, MainMenuScreen)

    def test_game_over_menu_key_returns_to_main_menu(self):
        self.register()
        self.manager.current.handle_event(key(pygame.K_1))
        self.manager.current.handle_event(key(pygame.K_1))
        self.manager.current.handle_event(key(pygame.K_2))
        game = self.manager.current
        game.handle_event(key(pygame.K_RIGHT))
        game.update(10.0)
        self.manager.current.handle_event(key(pygame.K_m))
        self.assertIsInstance(self.manager.current, MainMenuScreen)
        self.assertEqual(self.manager.depth, 1)


if __name__ == "__main__":
    unittest.main()
