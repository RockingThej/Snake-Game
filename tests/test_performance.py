"""Performance guards for the engine (S2-03, SNAKE-NF-001/NF-002).

The SRS needs at least 30 FPS, so a whole frame has 33.3 ms. The engine's share
of that is tiny (see benchmarks/engine_benchmark.py for real numbers); these
tests use budgets with a lot of headroom so they do not fail on a slow CI
machine, yet still catch a change that makes an operation scale badly, such as
going back to scanning the whole snake or board on every step.
"""
import random
import time
import unittest

from engine import collision
from engine.food import spawn_food
from engine.game_state import GameState
from engine.snake import Direction, Snake

FRAME_BUDGET_US = 1_000_000 / 30        # 33.3 ms per frame at 30 FPS


def mean_us(fn, repeat, rounds=3):
    """Mean microseconds per call; best of several rounds to ignore hiccups."""
    best = None
    for _ in range(rounds):
        start = time.perf_counter()
        for _ in range(repeat):
            fn()
        per_call = (time.perf_counter() - start) / repeat * 1e6
        best = per_call if best is None else min(best, per_call)
    return best


class TestEngineBudgets(unittest.TestCase):
    def test_collision_check_does_not_scale_with_snake_length(self):
        # A 5000-segment snake: scanning the body each tick costs ~100 us,
        # the O(1) check costs well under 1 us.
        snake = Snake((6000, 0), Direction.RIGHT, length=5000)
        cost = mean_us(lambda: collision.check(snake, 12000, 5), 2000)
        self.assertLess(cost, 40)

    def test_food_spawn_on_a_large_empty_board_is_cheap(self):
        rng = random.Random(1)
        occupied = {(x, y) for x in range(5) for y in range(5)}
        cost = mean_us(lambda: spawn_food(100, 100, occupied, rng), 200)
        self.assertLess(cost, 300)

    def test_food_spawn_still_finds_the_last_free_cell(self):
        occupied = {(x, y) for x in range(100) for y in range(100)}
        occupied.discard((99, 99))
        self.assertEqual(spawn_food(100, 100, occupied, random.Random(1)),
                         (99, 99))

    def test_tick_uses_a_small_part_of_the_frame_budget(self):
        for mode in ("classic", "obstacle", "survival"):
            with self.subTest(mode=mode):
                games = []
                for seed in range(30):
                    game = GameState(mode=mode, rng=random.Random(seed))
                    game.start()
                    games.append(game)

                def run_ticks():
                    for game in games:
                        game.tick()

                per_tick = mean_us(run_ticks, 1, rounds=5) / len(games)
                self.assertLess(per_tick, FRAME_BUDGET_US / 30)   # < 1.1 ms

    def test_eating_tick_stays_within_budget(self):
        for mode in ("classic", "obstacle", "survival"):
            with self.subTest(mode=mode):
                total, runs = 0.0, 40
                for seed in range(runs):
                    game = GameState(mode=mode, rng=random.Random(seed))
                    game.start()
                    hx, hy = game.snake.head
                    dx, dy = game.snake.direction.value
                    game.food = (hx + dx, hy + dy)
                    start = time.perf_counter()
                    game.tick()
                    total += time.perf_counter() - start
                self.assertLess(total / runs * 1e6, FRAME_BUDGET_US / 30)

    def test_survival_level_up_fits_inside_one_frame(self):
        total, runs = 0.0, 20
        for seed in range(runs):
            game = GameState(mode="survival", rng=random.Random(seed))
            game.start()
            game.foods_eaten = 2
            hx, hy = game.snake.head
            dx, dy = game.snake.direction.value
            game.food = (hx + dx, hy + dy)
            start = time.perf_counter()
            game.tick()
            total += time.perf_counter() - start
            self.assertEqual(game.level, 2)
        self.assertLess(total / runs * 1e6, FRAME_BUDGET_US)

    def test_creating_an_obstacle_game_fits_inside_a_few_frames(self):
        cost = mean_us(
            lambda: GameState(mode="obstacle", rng=random.Random(1)),
            10, rounds=3)
        self.assertLess(cost, FRAME_BUDGET_US * 3)


if __name__ == "__main__":
    unittest.main()
