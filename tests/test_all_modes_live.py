"""End-to-end headless gameplay test across all 5 game modes."""
import os
import unittest
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
pygame.init()

from modes import GameModeManager
from ui.game_screen import GameScreen
from ui.screen_manager import ScreenManager
from ui.menu_screens import BattleResultsScreen, GameOverScreen


class TestAllGameModesLive(unittest.TestCase):
    def setUp(self):
        self.surface = pygame.Surface((900, 640))
        self.modes = GameModeManager()

    def test_classic_mode_live(self):
        state = self.modes.create_game("classic", width=15, height=10)
        screen = GameScreen(state)
        manager = ScreenManager()
        manager.push(screen)
        screen.draw(self.surface)

        state.start()
        for _ in range(5):
            screen.update(state.tick_interval_ms / 1000 + 0.001)
            screen.draw(self.surface)

        # Force wall collision
        state.snake.move()
        while state.status.value == "running":
            state.snake.move()
            state.tick()

        screen.draw(self.surface)
        self.assertEqual(state.status.value, "game_over")
        self.assertIn("Game over", screen.message())

    def test_obstacle_mode_live(self):
        state = self.modes.create_game("obstacle", width=15, height=10)
        self.assertGreater(len(state.obstacles), 0)
        screen = GameScreen(state)
        manager = ScreenManager()
        manager.push(screen)
        screen.draw(self.surface)

        state.start()
        for _ in range(5):
            screen.update(state.tick_interval_ms / 1000 + 0.001)
            screen.draw(self.surface)

        self.assertEqual(state.mode, "obstacle")

    def test_power_up_mode_live(self):
        state = self.modes.create_game("power_up", width=15, height=10)
        self.assertGreaterEqual(len(state.powerups), 1)
        screen = GameScreen(state)
        manager = ScreenManager()
        manager.push(screen)
        screen.draw(self.surface)

        state.start()
        # Collect power-up
        name, pos = state.powerups[0]
        state.snake.body[0] = (pos[0] - 1, pos[1])
        from engine.snake import Direction
        state.snake.direction = Direction.RIGHT
        state.snake._pending = Direction.RIGHT

        screen.update(state.tick_interval_ms / 1000 + 0.001)
        screen.draw(self.surface)

        self.assertIn(name, state.active_powerups)
        self.assertIn("Active:", screen.hud_text())

    def test_survival_mode_live(self):
        state = self.modes.create_game("survival", width=15, height=10)
        screen = GameScreen(state)
        manager = ScreenManager()
        manager.push(screen)
        screen.draw(self.surface)

        state.start()
        # Eat 3 foods to trigger level up
        for _ in range(3):
            state.snake.grow()
            state.foods_eaten += 1
            state.rules.on_food_eaten(state)

        self.assertEqual(state.level, 2)
        screen.draw(self.surface)
        self.assertIn("Level: 2", screen.hud_text())

    def test_two_player_battle_mode_live(self):
        state = self.modes.create_game("two_player_battle", width=18, height=10)
        screen = GameScreen(state)
        manager = ScreenManager()
        manager.push(screen)
        screen.draw(self.surface)

        state.start()
        screen.update(state.tick_interval_ms / 1000 + 0.001)
        screen.draw(self.surface)

        # Draw collision
        from engine.snake import Direction, Snake
        state.snakes["player1"] = Snake((5, 5), Direction.RIGHT, length=1)
        state.snakes["player2"] = Snake((7, 5), Direction.LEFT, length=1)
        screen.update(state.tick_interval_ms / 1000 + 0.001)

        self.assertIsNone(state.winner)
        self.assertIsInstance(manager.current, BattleResultsScreen)
        manager.current.draw(self.surface)
        self.assertEqual(manager.current.winner_text(), "Draw")


if __name__ == "__main__":
    unittest.main()
