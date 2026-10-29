"""Menu and flow screens for selecting a mode, difficulty, and replay state."""

try:
    import pygame
except ImportError:  # pragma: no cover - optional runtime dependency
    pygame = None

from engine.game_state import GameState
from modes import GameModeManager
from ui.game_screen import GameScreen
from ui.screen_manager import Screen


def _require_pygame():
    if pygame is None:  # pragma: no cover - handled by skip decorators in tests
        raise RuntimeError("Pygame is required for UI screens")


def _safe_font(size=28):
    try:
        return pygame.font.SysFont(None, size)
    except Exception:  # pragma: no cover - font backend may be missing
        return None


class BaseMenuScreen(Screen):
    """Shared rendering helpers for menu screens."""

    def __init__(self, title, message=""):
        self.title = title
        self.message = message

    def _draw_text(self, surface, text, pos, color=(230, 230, 230), center=False):
        _require_pygame()
        font = _safe_font()
        if font is None:
            return
        image = font.render(text, True, color)
        rect = image.get_rect()
        if center:
            rect.center = pos
        else:
            rect.topleft = pos
        surface.blit(image, rect)

    def _draw_title(self, surface):
        self._draw_text(
            surface,
            self.title,
            (surface.get_width() // 2, 30),
            color=(255, 220, 120),
            center=True,
        )

    def draw(self, surface):
        _require_pygame()
        surface.fill((20, 20, 24))
        self._draw_title(surface)
        if self.message:
            self._draw_text(
                surface,
                self.message,
                (surface.get_width() // 2, surface.get_height() - 30),
                color=(255, 170, 120),
                center=True,
            )


class MainMenuScreen(BaseMenuScreen):
    """Initial landing screen for the game."""

    def __init__(self, title="Snake Game"):
        super().__init__(title)

    def handle_event(self, event):
        _require_pygame()
        if event.type != pygame.KEYDOWN:
            return

        if event.key in (pygame.K_1, pygame.K_RETURN, pygame.K_SPACE):
            if self.manager is not None:
                self.manager.replace(ModeSelectionScreen())
            return
        if event.key == pygame.K_ESCAPE:
            if self.manager is not None:
                self.manager.running = False
                self.manager._stack.clear()

    def draw(self, surface):
        super().draw(surface)
        _require_pygame()
        options = [
            "1. Play",
            "2. Difficulty",
            "3. Exit",
        ]
        for index, option in enumerate(options):
            self._draw_text(surface, option, (80, 100 + index * 40))


class ModeSelectionScreen(BaseMenuScreen):
    """Pick the game mode from the registry."""

    def __init__(self, mode_manager=None, title="Select a game mode"):
        self.mode_manager = mode_manager or GameModeManager()
        super().__init__(title)
        self.message = ""

    def mode_text(self):
        lines = [self.title]
        for mode in self.mode_manager.list_modes():
            status = "available" if mode.implemented else "coming soon"
            lines.append(f"{mode.selection_key}. {mode.name} - {status}")
        return "\n".join(lines)

    def handle_event(self, event):
        _require_pygame()
        if event.type != pygame.KEYDOWN:
            return

        mapping = {
            pygame.K_1: "1",
            pygame.K_2: "2",
            pygame.K_3: "3",
            pygame.K_4: "4",
            pygame.K_5: "5",
        }
        key = mapping.get(event.key)
        if key is None:
            return

        mode = self.mode_manager.select_mode(key)
        if not mode.implemented:
            self.message = f"{mode.name} is coming soon"
            return

        state = self.mode_manager.create_game(
            mode.id,
            width=30,
            height=20,
            difficulty="medium",
        )
        if self.manager is not None:
            self.manager.replace(DifficultySelectionScreen(state))

    def draw(self, surface):
        super().draw(surface)
        _require_pygame()
        for index, mode in enumerate(self.mode_manager.list_modes()):
            status = "available" if mode.implemented else "coming soon"
            color = (130, 240, 155) if mode.implemented else (180, 180, 190)
            self._draw_text(
                surface,
                f"{mode.selection_key}. {mode.name} - {status}",
                (80, 100 + index * 40),
                color=color,
            )


class DifficultySelectionScreen(BaseMenuScreen):
    """Choose the travel speed before the game begins."""

    def __init__(self, state, title="Select difficulty"):
        self.state = state or GameState(width=30, height=20)
        super().__init__(title)

    def handle_event(self, event):
        _require_pygame()
        if event.type != pygame.KEYDOWN:
            return

        mapping = {
            pygame.K_1: "easy",
            pygame.K_2: "medium",
            pygame.K_3: "hard",
        }
        difficulty = mapping.get(event.key)
        if difficulty is None:
            return

        self.state.set_difficulty(difficulty)
        if self.manager is not None:
            self.manager.replace(GameScreen(self.state))

    def draw(self, surface):
        super().draw(surface)
        _require_pygame()
        options = [
            "1. Easy",
            "2. Medium",
            "3. Hard",
        ]
        for index, option in enumerate(options):
            self._draw_text(surface, option, (80, 100 + index * 40))


class GameOverScreen(BaseMenuScreen):
    """Summary screen that shows the final score and post-game choices."""

    def __init__(self, state, title="Game Over"):
        self.state = state
        super().__init__(title)

    def score_text(self):
        return f"Final Score: {self.state.score}"

    def handle_event(self, event):
        _require_pygame()
        if event.type != pygame.KEYDOWN:
            return

        if event.key in (pygame.K_r, pygame.K_RETURN, pygame.K_SPACE):
            if self.manager is not None:
                state = GameState(
                    width=self.state.width,
                    height=self.state.height,
                    mode=self.state.mode,
                    difficulty=self.state.difficulty,
                )
                state.start()
                self.manager.replace(GameScreen(state))
            return

        if event.key in (pygame.K_m, pygame.K_ESCAPE):
            if self.manager is not None:
                self.manager.replace(MainMenuScreen())

    def draw(self, surface):
        super().draw(surface)
        _require_pygame()
        self._draw_text(
            surface,
            self.score_text(),
            (surface.get_width() // 2, 140),
            center=True,
            color=(255, 220, 120),
        )
        self._draw_text(surface, "R. Restart", (80, 200))
        self._draw_text(surface, "M. Menu", (80, 240))
