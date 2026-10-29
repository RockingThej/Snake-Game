"""S1-13: game board rendering and HUD.

GameScreen draws a GameState (engine/game_state.py) and runs its tick loop.
It replaces the drawing and game loop that lived in play_classic.py.
"""
import pygame

from engine.game_state import Status
from ui.input_handler import InputHandler
from ui.keymaps import SINGLE_PLAYER_KEYS

CELL = 30
HUD_HEIGHT = 40
BACKGROUND = (20, 20, 24)
BODY = (60, 200, 90)
HEAD = (140, 255, 160)
FOOD = (230, 70, 70)
OBSTACLE = (110, 110, 125)
TEXT = (230, 230, 230)
WARNING = (255, 220, 120)

DIFFICULTY_KEYS = {pygame.K_1: "easy", pygame.K_2: "medium", pygame.K_3: "hard"}


def window_size(state):
    """Window size in pixels needed to show the whole board and the HUD."""
    return state.width * CELL, state.height * CELL + HUD_HEIGHT


def cell_rect(x, y, inset=1):
    """Pixel rectangle of board cell (x, y), shrunk by inset pixels on each side."""
    return pygame.Rect(x * CELL + inset, y * CELL + HUD_HEIGHT + inset,
                       CELL - 2 * inset, CELL - 2 * inset)


class GameScreen:
    """Shows one game and plays it. Esc leaves, P pauses, R restarts after game over."""

    manager = None

    def __init__(self, state, input_handler=None, new_game=None):
        self.state = state
        self.input_handler = input_handler or InputHandler(SINGLE_PLAYER_KEYS)
        self._new_game = new_game
        self.elapsed = 0.0
        self.font = None

    def on_enter(self):
        try:
            self.font = pygame.font.SysFont(None, 28)
        except Exception:  # pragma: no cover - font backend may be missing
            self.font = None

    def restart(self):
        """Start a fresh game with the same mode, board size and difficulty."""
        if self._new_game is not None:
            self.state = self._new_game()
        else:
            from modes import GameModeManager
            old = self.state
            self.state = GameModeManager().create_game(
                old.mode, width=old.width, height=old.height,
                difficulty=old.difficulty)
        self.elapsed = 0.0

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        key, state = event.key, self.state
        if key == pygame.K_ESCAPE:
            if self.manager is not None:
                self.manager.pop()
        elif state.status == Status.PAUSED:
            if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_p):
                state.resume()
        elif state.status == Status.GAME_OVER:
            if key == pygame.K_r:
                self.restart()
        elif state.status == Status.RUNNING and key == pygame.K_p:
            state.pause()
            self.elapsed = 0.0
        elif state.status == Status.READY and key in DIFFICULTY_KEYS:
            state.set_difficulty(DIFFICULTY_KEYS[key])
        else:
            if state.status == Status.READY:
                state.start()
            resolved = self.input_handler.resolve(key)
            if resolved is not None and resolved[0] == "player1":
                state.set_direction(resolved[1])

    def update(self, dt):
        """Advance the game. dt is the seconds since the last frame."""
        if self.state.status != Status.RUNNING:
            self.elapsed = 0.0
            return
        self.elapsed += dt * 1000
        while self.elapsed >= self.state.tick_interval_ms:
            self.elapsed -= self.state.tick_interval_ms
            self.state.tick()

    def draw(self, surface):
        state = self.state
        surface.fill(BACKGROUND)
        for x, y in state.obstacles:
            pygame.draw.rect(surface, OBSTACLE, cell_rect(x, y))
        for x, y in state.snake.body:
            pygame.draw.rect(surface, BODY, cell_rect(x, y))
        pygame.draw.rect(surface, HEAD, cell_rect(*state.snake.head))
        if state.food:
            pygame.draw.rect(surface, FOOD, cell_rect(*state.food, inset=4))
        self._text(surface, self.hud_text(), (10, 10))
        message = self.message()
        if state.status == Status.PAUSED:
            overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            surface.blit(overlay, (0, 0))
        if message:
            self._text(surface, message, (surface.get_width() // 2,
                                          surface.get_height() // 2),
                       center=True)

    def hud_text(self):
        s = self.state
        return "Score: %d   Mode: %s   Difficulty: %s" % (
            s.score, s.mode.replace("_", " ").title(), s.difficulty.title())

    def message(self):
        s = self.state
        if s.status == Status.READY:
            return "1: Easy  2: Medium  3: Hard  |  Any move key: Start"
        if s.status == Status.PAUSED:
            return "PAUSED - press Enter or P to resume"
        if s.status == Status.GAME_OVER:
            return "Game over (%s) - R: restart, Esc: back" % (
                s.collision.value if s.collision else "win")
        return ""

    def _text(self, surface, text, pos, center=False):
        if self.font is None:
            return
        image = self.font.render(text, True, WARNING if center else TEXT)
        rect = image.get_rect()
        if center:
            rect.center = pos
        else:
            rect.topleft = pos
        surface.blit(image, rect)


def main():
    """Dev entry point: python -m ui.game_screen"""
    from modes import GameModeManager
    from ui.screen_manager import ScreenManager
    state = GameModeManager().create_game("classic", width=30, height=20)
    ScreenManager().run(GameScreen(state), size=window_size(state))


if __name__ == "__main__":
    main()
