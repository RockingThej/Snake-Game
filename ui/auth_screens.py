"""Authentication screens for login and registration."""

from __future__ import annotations

try:
    import pygame
except ImportError:  # pragma: no cover - optional runtime dependency
    pygame = None


class TextField:
    """Minimal text input field supporting focus and masking."""

    def __init__(self, label, value="", masked=False):
        self.label = label
        self.value = value
        self.masked = masked
        self.focused = False

    def display_text(self):
        if not self.masked:
            return self.value
        if not self.value:
            return ""
        return "*" * len(self.value)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and self.focused:
            if event.key in (pygame.K_RETURN, pygame.K_TAB):
                return
            if event.key == pygame.K_BACKSPACE:
                self.value = self.value[:-1]
            elif event.unicode and event.unicode.isprintable():
                self.value += event.unicode


class BaseAuthScreen:
    """Common helpers for login and register screens."""

    def __init__(self, auth, on_success=None):
        self.auth = auth
        self.on_success = on_success or (lambda username: None)
        self.message = ""
        self.focus_index = 0
        self.fields = []

    def add_field(self, field):
        self.fields.append(field)

    def move_focus(self, step=1):
        if not self.fields:
            return
        self.focus_index = (self.focus_index + step) % len(self.fields)
        for index, field in enumerate(self.fields):
            field.focused = index == self.focus_index

    def handle_event(self, event):
        if pygame is None:
            return
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_TAB, pygame.K_DOWN):
                self.move_focus(1)
                return
            if event.key == pygame.K_UP:
                self.move_focus(-1)
                return
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.submit()
                return

    def submit(self):
        raise NotImplementedError


class LoginScreen(BaseAuthScreen):
    """A simple login form."""

    def __init__(self, auth, on_success=None):
        super().__init__(auth, on_success)
        self.username = TextField("Username")
        self.password = TextField("Password", masked=True)
        self.add_field(self.username)
        self.add_field(self.password)
        self.move_focus(0)

    def submit(self):
        username = self.username.value.strip()
        password = self.password.value.strip()

        if not username or not password:
            self.message = "Enter your username and password"
            return

        if not self.auth.login(username, password):
            self.message = "Invalid username or password"
            return

        self.message = ""
        self.on_success(username)


class RegisterScreen(BaseAuthScreen):
    """A simple registration form."""

    def __init__(self, auth, on_success=None):
        super().__init__(auth, on_success)
        self.username = TextField("Username")
        self.password = TextField("Password", masked=True)
        self.confirm_password = TextField("Confirm Password", masked=True)
        self.add_field(self.username)
        self.add_field(self.password)
        self.add_field(self.confirm_password)
        self.move_focus(0)

    def submit(self):
        username = self.username.value.strip()
        password = self.password.value.strip()
        confirm = self.confirm_password.value.strip()

        if len(username) < 3:
            self.message = "Username must be at least 3 characters"
            return
        if len(password) < 6:
            self.message = "Password must be at least 6 characters"
            return
        if password != confirm:
            self.message = "Passwords do not match"
            return
        try:
            self.auth.register(username, password)
        except ValueError as exc:
            self.message = str(exc)
            return

        self.message = ""
        if self.on_success is not None:
            self.on_success(username)
