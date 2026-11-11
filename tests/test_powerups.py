"""Tests for the power-up system."""
import unittest

from engine.game_state import GameState
from modes.manager import GameModeManager


class TestPowerUps(unittest.TestCase):
    def test_power_up_mode_is_registered_and_creatable(self):
        state = GameModeManager().create_game("power_up", width=12, height=10)

        self.assertIsInstance(state, GameState)
        self.assertEqual(state.mode, "power_up")

    def test_speed_boost_applies_and_expires(self):
        state = GameState(width=12, height=10, mode="power_up")
        original = state.tick_interval_ms

        state.apply_power_up("speed_boost")
        self.assertLess(state.tick_interval_ms, original)

        state.powerup_manager.update(1000 * 30)
        self.assertEqual(state.tick_interval_ms, original)

    def test_slow_down_applies_and_expires(self):
        state = GameState(width=12, height=10, mode="power_up")
        original = state.tick_interval_ms

        state.apply_power_up("slow_down")
        self.assertGreater(state.tick_interval_ms, original)

        state.powerup_manager.update(1000 * 30)
        self.assertEqual(state.tick_interval_ms, original)

    def test_shield_and_score_multiplier_are_armed(self):
        state = GameState(width=12, height=10, mode="power_up")

        state.apply_power_up("shield")
        state.apply_power_up("score_multiplier")

        self.assertIn("shield", state.active_powerups)
        self.assertIn("score_multiplier", state.active_powerups)

    def test_snake_shrink_reduces_length(self):
        state = GameState(width=12, height=10, mode="power_up")
        state.snake.grow(2)
        state.snake.move()
        state.snake.move()
        before = len(state.snake.body)

        state.apply_power_up("snake_shrink")

        self.assertLess(len(state.snake.body), before)

    def test_power_up_spawns_at_setup(self):
        state = GameState(width=12, height=10, mode="power_up")
        self.assertGreaterEqual(len(state.powerups), 1)
        name, pos = state.powerups[0]
        self.assertIn(name, ("speed_boost", "slow_down", "shield", "score_multiplier", "snake_shrink"))
        self.assertTrue(0 <= pos[0] < 12 and 0 <= pos[1] < 10)

    def test_collecting_power_up_activates_it(self):
        from engine.snake import Direction, Snake
        from engine.game_state import Status

        state = GameState(width=12, height=10, mode="power_up")
        state.snake = Snake((5, 5), Direction.RIGHT, length=3)
        state.powerups = [("shield", (6, 5))]
        state.start()

        state.tick()

        self.assertEqual(state.status, Status.RUNNING)
        self.assertEqual(state.powerups, [])
        self.assertIn("shield", state.active_powerups)

    def test_shield_absorbs_wall_collision(self):
        from engine.snake import Direction, Snake
        from engine.game_state import Status

        state = GameState(width=12, height=10, mode="power_up")
        state.snake = Snake((0, 5), Direction.LEFT, length=3)
        state.apply_power_up("shield")
        state.start()

        state.tick()

        # Snake should not die; shield should be consumed and snake moved back to (0, 5)
        self.assertEqual(state.status, Status.RUNNING)
        self.assertNotIn("shield", state.active_powerups)
        self.assertEqual(state.snake.head, (0, 5))

    def test_score_multiplier_doubles_points(self):
        from engine.snake import Direction, Snake

        state = GameState(width=12, height=10, mode="power_up")
        state.snake = Snake((5, 5), Direction.RIGHT, length=3)
        state.food = (6, 5)
        state.apply_power_up("score_multiplier")
        state.start()

        state.tick()

        self.assertEqual(state.score, state.POINTS_PER_FOOD * 2)


if __name__ == "__main__":
    unittest.main()
