"""S1-13: game board rendering and HUD.

GameScreen draws a GameState (engine/game_state.py) and runs its tick loop.
It replaces the drawing and game loop that lived in play_classic.py.
"""
import pygame

from engine.game_state import Status
from ui.input_handler import InputHandler
from ui.keymaps import SINGLE_PLAYER_KEYS, TWO_PLAYER_KEYS

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
        default_keys = (
            TWO_PLAYER_KEYS if hasattr(state, "snakes") else SINGLE_PLAYER_KEYS
        )
        self.input_handler = input_handler or InputHandler(default_keys)
        self._new_game = new_game
        self.elapsed = 0.0
        self.font = None
        self._finished = False

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
            options = {
                "width": old.width,
                "height": old.height,
                "difficulty": old.difficulty,
            }
            if hasattr(old, "player_ids"):
                options["player_ids"] = old.player_ids
            self.state = GameModeManager().create_game(
                old.mode, **options)
        self.elapsed = 0.0
        self._finished = False

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
            if resolved is not None:
                player_id, direction = resolved
                if hasattr(state, "snakes"):
                    state.set_direction(direction, player_id)
                elif player_id == "player1":
                    state.set_direction(direction)

    def update(self, dt):
        """Advance the game. dt is the seconds since the last frame."""
        if self.state.status != Status.RUNNING:
            self.elapsed = 0.0
            return
        self.elapsed += dt * 1000
        while self.elapsed >= self.state.tick_interval_ms:
            self.elapsed -= self.state.tick_interval_ms
            self.state.tick()
        self._report_game_over()

    def _report_game_over(self):
        """Tell the session once when the game ends (saves the score)."""
        if self._finished or self.state.status != Status.GAME_OVER:
            return
        self._finished = True
        if hasattr(self.state, "scores") and self.manager is not None:
            from ui.menu_screens import BattleResultsScreen

            self.manager.replace(BattleResultsScreen(self.state))
            return
        session = getattr(self.manager, "session", None)
        if session is not None:
            session.finish_game(self.state)

    def draw(self, surface):
        state = self.state
        surface.fill(BACKGROUND)
        for x, y in state.obstacles:
            pygame.draw.rect(surface, OBSTACLE, cell_rect(x, y))
        snakes = (
            state.snakes if hasattr(state, "snakes")
            else {"player1": state.snake}
        )
        colors = {
            "player1": (BODY, HEAD),
            "player2": ((65, 130, 230), (145, 190, 255)),
        }
        for player, snake in snakes.items():
            body_color, head_color = colors.get(player, (BODY, HEAD))
            for x, y in snake.body:
                pygame.draw.rect(surface, body_color, cell_rect(x, y))
            pygame.draw.rect(surface, head_color, cell_rect(*snake.head))
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
        if hasattr(s, "scores"):
            return (
                f"P1: {s.scores['player1']}   P2: {s.scores['player2']}   "
                f"{s.mode.replace('_', ' ').title()}   "
                f"{s.difficulty.title()}"
            )
        return "Score: %d   Mode: %s   Difficulty: %s" % (
            s.score, s.mode.replace("_", " ").title(), s.difficulty.title())

    def message(self):
        s = self.state
        if s.status == Status.READY:
            if hasattr(s, "snakes"):
                return "P1: WASD  P2: Arrows  |  Any move key: Start"
            return "1: Easy  2: Medium  3: Hard  |  Any move key: Start"
        if s.status == Status.PAUSED:
            return "PAUSED - press Enter or P to resume"
        if s.status == Status.GAME_OVER:
            if hasattr(s, "snakes"):
                winner = s.winner.replace("player", "Player ").title()
                outcome = f"{winner} wins" if s.winner else "Draw"
                reason = s.collision.value if s.collision else "board full"
                return (
                    f"{outcome} ({reason}) - R: restart, Esc: back"
                )
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
