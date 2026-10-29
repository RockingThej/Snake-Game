"""Tests for the authentication screens and field behaviour."""
import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

try:
    import pygame  # noqa: E402
except ImportError:  # pragma: no cover - optional runtime dependency
    pygame = None

from ui.auth_screens import LoginScreen, RegisterScreen, TextField  # noqa: E402


class DummyAuth:
    def __init__(self):
        self.users = {"alice": "secret1"}

    def login(self, username, password):
        if username not in self.users:
            return False
        return self.users[username] == password

    def register(self, username, password):
        if username in self.users:
            raise ValueError("username already taken")
        self.users[username] = password
        return True


@unittest.skipIf(pygame is None, "pygame not installed")
class TestAuthScreens(unittest.TestCase):
    def test_login_empty_fields_shows_message(self):
        auth = DummyAuth()
        called = []
        screen = LoginScreen(auth, lambda user: called.append(user))

        screen.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))

        self.assertEqual(screen.message, "Enter your username and password")
        self.assertEqual(called, [])

    def test_login_wrong_credentials_show_invalid_message(self):
        auth = DummyAuth()
        screen = LoginScreen(auth, lambda user: None)
        screen.username.value = "alice"
        screen.password.value = "wrongpass"

        screen.submit()

        self.assertEqual(screen.message, "Invalid username or password")

    def test_login_success_calls_callback(self):
        auth = DummyAuth()
        called = []
        screen = LoginScreen(auth, lambda user: called.append(user))
        screen.username.value = "alice"
        screen.password.value = "secret1"

        screen.submit()

        self.assertEqual(called, ["alice"])
        self.assertEqual(screen.message, "")

    def test_register_validates_fields(self):
        auth = DummyAuth()
        screen = RegisterScreen(auth)
        screen.username.value = "ab"
        screen.password.value = "12345"
        screen.confirm_password.value = "12345"

        screen.submit()

        self.assertIn("at least 3", screen.message)

    def test_register_rejects_taken_username(self):
        auth = DummyAuth()
        screen = RegisterScreen(auth)
        screen.username.value = "alice"
        screen.password.value = "password"
        screen.confirm_password.value = "password"

        screen.submit()

        self.assertIn("taken", screen.message.lower())

    def test_text_field_tracks_masked_value(self):
        field = TextField("password", masked=True)
        field.value = "secret"

        self.assertEqual(field.display_text(), "******")


if __name__ == "__main__":
    unittest.main()
