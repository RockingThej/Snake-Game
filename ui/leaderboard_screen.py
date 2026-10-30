"""Leaderboard screen: shows the top personal bests."""

try:
    import pygame
except ImportError:  # pragma: no cover - optional runtime dependency
    pygame = None

from ui.screen_manager import Screen

BACKGROUND = (20, 20, 24)
TITLE = (255, 220, 120)
TEXT = (230, 230, 230)
MUTED = (180, 180, 190)


def format_row(rank, entry):
    mode = str(entry.get("mode", "")).replace("_", " ").title()
    difficulty = str(entry.get("difficulty", "")).title()
    return "%2d.  %-16s %5d   %s / %s" % (
        rank, entry["username"][:16], entry["score"], mode, difficulty)


class LeaderboardScreen(Screen):
    """Read-only list of leaderboard entries. Esc/Enter goes back."""

    def __init__(self, entries, title="Leaderboard", on_back=None):
        self.entries = list(entries)
        self.title = title
        self.on_back = on_back
        self.font = None

    def rows(self):
        return [format_row(i, e) for i, e in enumerate(self.entries, 1)]

    def on_enter(self):
        try:
            self.font = pygame.font.SysFont(None, 28)
        except Exception:  # pragma: no cover - font backend may be missing
            self.font = None

    def handle_event(self, event):
        if pygame is None or event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE,
                         pygame.K_BACKSPACE):
            if self.on_back is not None:
                self.on_back()
            elif self.manager is not None:
                self.manager.pop()

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
        self._text(surface, self.title, (surface.get_width() // 2, 40),
                   TITLE, center=True)
        rows = self.rows()
        if not rows:
            self._text(surface, "No scores yet - play a game!",
                       (surface.get_width() // 2, 140), MUTED, center=True)
        for index, row in enumerate(rows):
            self._text(surface, row, (80, 100 + index * 36))
        self._text(surface, "Esc: back",
                   (surface.get_width() // 2, surface.get_height() - 30),
                   MUTED, center=True)
