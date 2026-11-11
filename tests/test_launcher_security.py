"""S2-17: the real launcher (main.build_app) with session and security
safeguards switched on (TC-AUTH-003, TC-SEC-003, TC-SEC-005)."""
import os
import shutil
import tempfile
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

try:
    import pygame
    from auth.guarded_session import GuardedSession
    from auth.session_manager import SessionManager
    from db import admin_repository, get_user_by_username
    from main import build_app
    from ui.auth_screens import LoginScreen, RegisterScreen
    from ui.menu_screens import MainMenuScreen
except ImportError:  # pygame is not installed
    pygame = None


def key(code, char=""):
    return pygame.event.Event(pygame.KEYDOWN, key=code, unicode=char)


def type_text(screen, text):
    for char in text:
        screen.handle_event(key(ord(char), char))


@unittest.skipIf(pygame is None, "pygame not installed")
class TestLauncherSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.db = os.path.join(self.tmp, "launcher.sqlite3")
        self.manager, first = build_app(self.db)
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
        return screen

    def log_in(self, name, password):
        screen = self.manager.current
        self.assertIsInstance(screen, LoginScreen)
        type_text(screen, name)
        screen.handle_event(key(pygame.K_TAB))
        type_text(screen, password)
        screen.handle_event(key(pygame.K_RETURN))
        return screen

    def test_launcher_uses_the_guarded_session(self):
        self.assertIsInstance(self.manager.session, GuardedSession)

    def test_logging_out_from_the_menu_ends_the_server_session(self):
        self.register()
        session = self.manager.session
        token = session.token
        self.assertTrue(SessionManager(self.db).is_active(token))

        self.manager.current.handle_event(key(pygame.K_3))   # log out

        self.assertIsInstance(self.manager.current, LoginScreen)
        self.assertFalse(SessionManager(self.db).is_active(token))
        self.assertFalse(session.logged_in)

    def test_a_huge_password_on_the_login_screen_does_not_crash(self):
        self.register()
        self.manager.current.handle_event(key(pygame.K_3))   # log out
        screen = self.log_in("alice1", "x" * 150)
        self.assertIsInstance(self.manager.current, LoginScreen)
        self.assertEqual(screen.message, "Invalid username or password")

    def test_registration_rejects_a_username_with_odd_characters(self):
        screen = self.register(name="bad name<1>")
        self.assertIsInstance(self.manager.current, RegisterScreen)
        self.assertIn("Username must be", screen.message)
        self.assertIsNone(get_user_by_username("bad name<1>",
                                               db_path=self.db))

    def test_registration_rejects_an_oversized_password(self):
        screen = self.register(password="p" * 100)
        self.assertIsInstance(self.manager.current, RegisterScreen)
        self.assertIn("at most 72", screen.message)

    def test_a_disabled_account_cannot_log_in_through_the_screen(self):
        self.register()
        user_id = get_user_by_username("alice1", db_path=self.db)["id"]
        self.manager.current.handle_event(key(pygame.K_3))   # log out
        admin_repository.set_account_disabled(user_id, True, "test", None,
                                              db_path=self.db)
        screen = self.log_in("alice1", "secret123")
        self.assertIsInstance(self.manager.current, LoginScreen)
        self.assertEqual(screen.message, "Invalid username or password")

    def test_a_normal_login_still_works(self):
        self.register()
        self.manager.current.handle_event(key(pygame.K_3))   # log out
        self.log_in("alice1", "secret123")
        self.assertIsInstance(self.manager.current, MainMenuScreen)
        self.assertTrue(self.manager.session.logged_in)


if __name__ == "__main__":
    unittest.main()
