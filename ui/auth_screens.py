"""Authentication screens for login and registration."""

from __future__ import annotations

try:
    import pygame
except ImportError:  # pragma: no cover - optional runtime dependency
    pygame = None

from ui.screen_manager import Screen


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


BACKGROUND = (20, 20, 24)
TITLE = (255, 220, 120)
TEXT = (230, 230, 230)
MUTED = (180, 180, 190)
ERROR = (255, 150, 120)
FIELD = (40, 40, 48)
FIELD_FOCUSED = (70, 90, 130)


class BaseAuthScreen(Screen):
    """Common helpers for login and register screens."""

    title = ""
    hint = ""

    def __init__(self, auth, on_success=None, on_switch=None, on_cancel=None):
        self.auth = auth
        self.on_success = on_success or (lambda username: None)
        self.on_switch = on_switch    # F2: jump to the other form
        self.on_cancel = on_cancel    # Esc; default closes this screen
        self.message = ""
        self.focus_index = 0
        self.fields = []
        self.font = None

    def add_field(self, field):
        self.fields.append(field)

    def move_focus(self, step=1):
        if not self.fields:
            return
        self.focus_index = (self.focus_index + step) % len(self.fields)
        for index, field in enumerate(self.fields):
            field.focused = index == self.focus_index

    def on_enter(self):
        try:
            self.font = pygame.font.SysFont(None, 28)
        except Exception:  # pragma: no cover - font backend may be missing
            self.font = None

    def handle_event(self, event):
        if pygame is None:
            return
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            if self.on_cancel is not None:
                self.on_cancel()
            elif self.manager is not None:
                self.manager.pop()
            return
        if event.key == pygame.K_F2:
            if self.on_switch is not None:
                self.on_switch()
            return
        if event.key in (pygame.K_TAB, pygame.K_DOWN):
            self.move_focus(1)
            return
        if event.key == pygame.K_UP:
            self.move_focus(-1)
            return
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.submit()
            return
        if self.fields:
            self.fields[self.focus_index].handle_event(event)

    def submit(self):
        raise NotImplementedError

    def _text(self, surface, text, pos, color=TEXT, center=False):
        if self.font is None:
            # on_enter can run before pygame.init(), so load lazily here
            try:
                self.font = pygame.font.SysFont(None, 28)
            except Exception:  # pragma: no cover - font backend missing
                return
        image = self.font.render(text, True, color)
        rect = image.get_rect()
        if center:
            rect.center = pos
        else:
            rect.topleft = pos
        surface.blit(image, rect)

    def draw(self, surface):
        surface.fill(BACKGROUND)
        width = surface.get_width()
        self._text(surface, self.title, (width // 2, 70), TITLE, center=True)
        left = width // 2 - 200
        y = 150
        for field in self.fields:
            self._text(surface, field.label, (left, y), MUTED)
            box = pygame.Rect(left, y + 26, 400, 36)
            colour = FIELD_FOCUSED if field.focused else FIELD
            pygame.draw.rect(surface, colour, box, border_radius=4)
            shown = field.display_text() + ("|" if field.focused else "")
            self._text(surface, shown, (box.x + 10, box.y + 8))
            y += 90
        if self.message:
            self._text(surface, self.message, (width // 2, y + 10), ERROR,
                       center=True)
        self._text(surface, self.hint,
                   (width // 2, surface.get_height() - 30), MUTED, center=True)


class LoginScreen(BaseAuthScreen):
    """A simple login form."""

    title = "Log in"
    hint = "Tab: next field   Enter: log in   F2: create account   Esc: quit"

    def __init__(self, auth, on_success=None, on_switch=None, on_cancel=None):
        super().__init__(auth, on_success, on_switch, on_cancel)
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

    title = "Create account"
    hint = "Tab: next field   Enter: register   F2: log in   Esc: back"

    def __init__(self, auth, on_success=None, on_switch=None, on_cancel=None):
        super().__init__(auth, on_success, on_switch, on_cancel)
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
