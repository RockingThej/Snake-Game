"""Survival Mode (S2-02): progressive difficulty (TC-SURVIVAL-001)."""
import random
import unittest

from engine.collision import Collision
from engine.game_state import GameState, Status
from engine.obstacles import is_connected
from modes import GameModeManager
from modes.rules import SurvivalRules


def survival_game(seed=0, **options):
    game = GameState(mode="survival", rng=random.Random(seed), **options)
    game.start()
    return game


def eat(game, times=1):
    """Eat ``times`` foods through real ticks by putting food straight ahead.

    The snake starts mid-board heading right, so this is good for up to six
    foods before it would reach the wall.
    """
    for _ in range(times):
        hx, hy = game.snake.head
        dx, dy = game.snake.direction.value
        game.food = (hx + dx, hy + dy)
        before = game.foods_eaten
        game.tick()
        assert game.status == Status.RUNNING
        assert game.foods_eaten == before + 1


def fast_forward(game, levels):
    """Jump ``levels`` levels ahead, running the same hook a tick would."""
    for _ in range(levels):
        game.foods_eaten += SurvivalRules.FOODS_PER_LEVEL
        game.rules.on_food_eaten(game)


class TestLevels(unittest.TestCase):
    def test_starts_at_level_one_with_difficulty_speed(self):
        game = survival_game(difficulty="medium")
        self.assertEqual(game.level, 1)
        self.assertEqual(game.tick_interval_ms, 110)

    def test_level_formula(self):
        rules = SurvivalRules()
        self.assertEqual(rules.level_for(0), 1)
        self.assertEqual(rules.level_for(rules.FOODS_PER_LEVEL - 1), 1)
        self.assertEqual(rules.level_for(rules.FOODS_PER_LEVEL), 2)
        self.assertEqual(rules.level_for(rules.FOODS_PER_LEVEL * 4), 5)

    def test_level_rises_after_enough_foods(self):
        game = survival_game()
        eat(game, SurvivalRules.FOODS_PER_LEVEL - 1)
        self.assertEqual(game.level, 1)
        eat(game, 1)
        self.assertEqual(game.level, 2)

    def test_speed_increases_with_each_level(self):
        game = survival_game(difficulty="medium")
        before = game.tick_interval_ms
        eat(game, SurvivalRules.FOODS_PER_LEVEL)
        self.assertEqual(game.tick_interval_ms,
                         before - SurvivalRules.SPEEDUP_MS)

    def test_speed_never_drops_below_the_minimum(self):
        rules = SurvivalRules()
        self.assertEqual(rules.interval_for(75, 1), 75)
        self.assertEqual(rules.interval_for(75, 100), rules.MIN_INTERVAL_MS)
        self.assertEqual(rules.interval_for(160, 100), rules.MIN_INTERVAL_MS)

    def test_starting_difficulty_sets_the_base_speed(self):
        easy = survival_game(difficulty="easy")
        hard = survival_game(difficulty="hard")
        self.assertGreater(easy.tick_interval_ms, hard.tick_interval_ms)

    def test_difficulty_chosen_before_start_is_respected(self):
        game = GameState(mode="survival", rng=random.Random(0))
        game.set_difficulty("hard")
        self.assertEqual(game.base_tick_interval_ms, 75)
        self.assertEqual(game.tick_interval_ms, 75)

    def test_classic_mode_never_speeds_up(self):
        game = GameState(rng=random.Random(0))
        game.start()
        eat(game, 6)
        self.assertEqual(game.foods_eaten, 6)
        self.assertEqual(game.tick_interval_ms, 110)
        self.assertEqual(game.level, 1)


class TestSurvivalObstacles(unittest.TestCase):
    def test_board_starts_without_obstacles(self):
        self.assertEqual(survival_game().obstacles, set())

    def test_obstacles_appear_on_level_up(self):
        game = survival_game()
        eat(game, SurvivalRules.FOODS_PER_LEVEL)
        self.assertEqual(len(game.obstacles),
                         SurvivalRules.OBSTACLES_PER_LEVEL)

    def test_new_obstacles_avoid_snake_food_and_path(self):
        for seed in range(15):
            game = survival_game(seed)
            eat(game, SurvivalRules.FOODS_PER_LEVEL)
            self.assertFalse(game.obstacles & game.snake.cells(), seed)
            self.assertNotIn(game.food, game.obstacles, seed)
            hx, hy = game.snake.head
            dx, dy = game.snake.direction.value
            for step in range(1, 7):
                self.assertNotIn((hx + dx * step, hy + dy * step),
                                 game.obstacles, seed)

    def test_free_cells_stay_connected_as_levels_rise(self):
        game = survival_game(2)
        for _ in range(10):
            fast_forward(game, 1)
            self.assertTrue(is_connected(game.width, game.height,
                                         game.obstacles))

    def test_obstacle_count_is_capped(self):
        game = survival_game(1)
        cap = int(game.width * game.height * SurvivalRules.MAX_DENSITY)
        fast_forward(game, 80)
        self.assertLessEqual(len(game.obstacles), cap)
        self.assertGreater(len(game.obstacles), 0)

    def test_hitting_a_new_obstacle_ends_the_game(self):
        game = survival_game()
        hx, hy = game.snake.head
        game.obstacles = {(hx + 1, hy)}
        game.tick()
        self.assertEqual(game.status, Status.GAME_OVER)
        self.assertEqual(game.collision, Collision.OBSTACLE)


class TestSurvivalRegistry(unittest.TestCase):
    def test_mode_is_implemented(self):
        manager = GameModeManager()
        self.assertTrue(manager.select_mode("survival").implemented)
        state = manager.create_game("survival", width=30, height=20)
        self.assertEqual(state.mode, "survival")
        self.assertEqual(state.level, 1)


if __name__ == "__main__":
    unittest.main()
