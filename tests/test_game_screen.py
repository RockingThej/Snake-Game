import os
import random
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

try:
    import pygame
    from engine.game_state import GameState, Status
    from engine.snake import Direction
    from ui.game_screen import GameScreen, cell_rect, window_size
    from ui.screen_manager import ScreenManager
except ImportError:  # pygame is not installed (for example in CI)
    pygame = None


def key(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k)


@unittest.skipIf(pygame is None, "pygame not installed")
class TestGameScreen(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def make(self):
        state = GameState(width=10, height=10, rng=random.Random(0))
        screen = GameScreen(state)
        manager = ScreenManager()
        manager.push(screen)
        screen.on_enter()
        return screen, manager

    def test_geometry(self):
        self.assertEqual(window_size(GameState(width=30, height=20)), (900, 640))
        self.assertEqual(cell_rect(0, 0).topleft, (1, 41))

    def test_nothing_moves_before_start(self):
        screen, _ = self.make()
        head = screen.state.snake.head
        screen.update(5.0)
        self.assertEqual(screen.state.snake.head, head)

    def test_move_key_starts_game_and_steers(self):
        screen, _ = self.make()
        screen.handle_event(key(pygame.K_UP))
        self.assertEqual(screen.state.status, Status.RUNNING)
        x, y = screen.state.snake.head
        screen.update(screen.state.tick_interval_ms / 1000 + 0.001)
        self.assertEqual(screen.state.snake.head, (x, y - 1))

    def test_update_runs_one_tick_per_interval(self):
        screen, _ = self.make()
        screen.handle_event(key(pygame.K_RIGHT))
        x, y = screen.state.snake.head
        screen.update(screen.state.tick_interval_ms * 2.5 / 1000)
        self.assertEqual(screen.state.snake.head, (x + 2, y))

    def test_difficulty_keys_before_start(self):
        screen, _ = self.make()
        screen.handle_event(key(pygame.K_3))
        self.assertEqual(screen.state.difficulty, "hard")
        self.assertEqual(screen.state.status, Status.READY)

    def test_pause_and_resume(self):
        screen, _ = self.make()
        screen.handle_event(key(pygame.K_RIGHT))
        screen.handle_event(key(pygame.K_p))
        self.assertEqual(screen.state.status, Status.PAUSED)
        head = screen.state.snake.head
        screen.update(5.0)
        self.assertEqual(screen.state.snake.head, head)
        screen.handle_event(key(pygame.K_RETURN))
        self.assertEqual(screen.state.status, Status.RUNNING)

    def test_restart_after_game_over(self):
        screen, _ = self.make()
        screen.handle_event(key(pygame.K_RIGHT))
        screen.update(10.0)
        self.assertEqual(screen.state.status, Status.GAME_OVER)
        screen.handle_event(key(pygame.K_r))
        self.assertEqual(screen.state.status, Status.READY)
        self.assertEqual(screen.state.score, 0)

    def test_escape_leaves_screen(self):
        screen, manager = self.make()
        screen.handle_event(key(pygame.K_ESCAPE))
        self.assertFalse(manager.running)

    def test_non_key_events_are_ignored(self):
        screen, _ = self.make()
        screen.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=(1, 1)))
        self.assertEqual(screen.state.status, Status.READY)

    def test_hud_and_draw_in_every_status(self):
        screen, _ = self.make()
        surface = pygame.Surface(window_size(screen.state))
        self.assertIn("Score: 0", screen.hud_text())
        self.assertIn("Classic", screen.hud_text())
        self.assertIn("Medium", screen.hud_text())
        screen.draw(surface)
        screen.handle_event(key(pygame.K_RIGHT))
        screen.draw(surface)
        screen.handle_event(key(pygame.K_p))
        screen.draw(surface)
        screen.handle_event(key(pygame.K_p))
        screen.update(10.0)
        self.assertIn("Game over", screen.message())
        screen.draw(surface)

    def test_obstacles_are_drawn(self):
        screen, _ = self.make()
        screen.state.obstacles = {(0, 0)}
        surface = pygame.Surface(window_size(screen.state))
        screen.draw(surface)
        self.assertEqual(surface.get_at((5, 45))[:3], (110, 110, 125))

    def test_wasd_keys_steer_the_snake(self):
        screen, _ = self.make()
        screen.handle_event(key(pygame.K_w))
        x, y = screen.state.snake.head
        screen.update(screen.state.tick_interval_ms / 1000 + 0.001)
        self.assertEqual(screen.state.snake.head, (x, y - 1))
        self.assertEqual(screen.state.snake.direction, Direction.UP)


if __name__ == "__main__":
    unittest.main()
