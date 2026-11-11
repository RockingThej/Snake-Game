"""Obstacle Mode (S2-01): placement, fairness, collision (TC-OBSTACLE-001)."""
import random
import unittest

from engine import collision
from engine.collision import Collision
from engine.food import spawn_food
from engine.game_state import GameState, Status
from engine.obstacles import (generate_obstacles, is_connected,
                              protected_cells)
from engine.snake import Direction, Snake
from modes import GameModeManager


def obstacle_game(seed=0, **options):
    return GameState(mode="obstacle", rng=random.Random(seed), **options)


class TestGenerateObstacles(unittest.TestCase):
    def test_places_requested_count(self):
        placed = generate_obstacles(20, 10, 8, set(), random.Random(1))
        self.assertEqual(len(placed), 8)

    def test_zero_or_negative_count_places_nothing(self):
        rng = random.Random(1)
        self.assertEqual(generate_obstacles(10, 10, 0, set(), rng), set())
        self.assertEqual(generate_obstacles(10, 10, -3, set(), rng), set())

    def test_stays_inside_the_board(self):
        placed = generate_obstacles(12, 7, 15, set(), random.Random(2))
        for x, y in placed:
            self.assertTrue(0 <= x < 12 and 0 <= y < 7)

    def test_never_uses_keep_free_or_existing_cells(self):
        keep_free = {(x, y) for x in range(5) for y in range(5)}
        existing = {(9, 9), (8, 9)}
        placed = generate_obstacles(10, 10, 30, keep_free, random.Random(3),
                                    existing=existing)
        self.assertFalse(placed & keep_free)
        self.assertFalse(placed & existing)

    def test_same_seed_gives_same_layout(self):
        a = generate_obstacles(30, 20, 24, set(), random.Random(7))
        b = generate_obstacles(30, 20, 24, set(), random.Random(7))
        self.assertEqual(a, b)

    def test_free_cells_stay_connected(self):
        for seed in range(10):
            placed = generate_obstacles(30, 20, 60, set(), random.Random(seed))
            self.assertTrue(is_connected(30, 20, placed), seed)

    def test_never_seals_off_a_cell_even_when_asked_for_too_many(self):
        # Asking for far more than fits must stop early, not wall anything in.
        placed = generate_obstacles(6, 6, 100, set(), random.Random(4))
        self.assertLess(len(placed), 36)
        self.assertTrue(is_connected(6, 6, placed))


class TestIsConnected(unittest.TestCase):
    def test_empty_board_is_connected(self):
        self.assertTrue(is_connected(5, 5, set()))

    def test_wall_across_the_board_disconnects_it(self):
        wall = {(2, y) for y in range(5)}
        self.assertFalse(is_connected(5, 5, wall))

    def test_wall_with_a_gap_stays_connected(self):
        wall = {(2, y) for y in range(4)}
        self.assertTrue(is_connected(5, 5, wall))

    def test_fully_blocked_board_counts_as_connected(self):
        full = {(x, y) for x in range(3) for y in range(3)}
        self.assertTrue(is_connected(3, 3, full))


class TestProtectedCells(unittest.TestCase):
    def test_includes_snake_and_path_ahead(self):
        snake = Snake((10, 10), Direction.RIGHT, length=3)
        cells = protected_cells(snake, 30, 20, ahead=6)
        self.assertTrue(snake.cells() <= cells)
        for step in range(1, 7):
            self.assertIn((10 + step, 10), cells)

    def test_includes_short_runs_towards_possible_turns(self):
        snake = Snake((10, 10), Direction.RIGHT, length=3)
        cells = protected_cells(snake, 30, 20)
        self.assertIn((10, 7), cells)    # up
        self.assertIn((10, 13), cells)   # down

    def test_is_clipped_to_the_board(self):
        snake = Snake((2, 0), Direction.UP, length=1)
        for x, y in protected_cells(snake, 10, 10):
            self.assertTrue(0 <= x < 10 and 0 <= y < 10)


class TestObstacleGame(unittest.TestCase):
    def test_game_starts_with_obstacles(self):
        game = obstacle_game()
        self.assertEqual(len(game.obstacles), 24)      # 4% of 30 x 20

    def test_classic_game_has_no_obstacles(self):
        self.assertEqual(GameState(rng=random.Random(0)).obstacles, set())

    def test_obstacles_never_on_snake_or_in_front_of_it(self):
        for seed in range(30):
            game = obstacle_game(seed)
            self.assertFalse(game.obstacles & game.snake.cells(), seed)
            hx, hy = game.snake.head
            for step in range(1, 7):
                self.assertNotIn((hx + step, hy), game.obstacles, seed)

    def test_food_never_spawns_on_an_obstacle(self):
        for seed in range(30):
            game = obstacle_game(seed)
            self.assertNotIn(game.food, game.obstacles, seed)

    def test_every_respawn_avoids_obstacles_and_snake(self):
        game = obstacle_game(3)
        for _ in range(300):
            cell = spawn_food(game.width, game.height, game._occupied(),
                              game.rng)
            self.assertNotIn(cell, game.obstacles)
            self.assertNotIn(cell, game.snake.cells())

    def test_free_cells_are_connected(self):
        for seed in range(15):
            game = obstacle_game(seed)
            self.assertTrue(is_connected(game.width, game.height,
                                         game.obstacles), seed)

    def test_hitting_an_obstacle_ends_the_game(self):
        game = obstacle_game()
        game.start()
        hx, hy = game.snake.head
        game.obstacles = {(hx + 1, hy)}
        game.tick()
        self.assertEqual(game.status, Status.GAME_OVER)
        self.assertEqual(game.collision, Collision.OBSTACLE)

    def test_avoiding_obstacles_keeps_the_game_running(self):
        game = obstacle_game()
        game.start()
        game.obstacles = {(0, 0)}          # far from the snake's path
        for _ in range(5):
            game.tick()
        self.assertEqual(game.status, Status.RUNNING)

    def test_collision_check_reports_obstacle_cell(self):
        snake = Snake((5, 5), Direction.RIGHT, length=1)
        snake.move()
        self.assertEqual(collision.check(snake, 10, 10, {(6, 5)}),
                         Collision.OBSTACLE)

    def test_obstacle_count_scales_with_board_size(self):
        small = GameState(width=10, height=10, mode="obstacle",
                          rng=random.Random(0))
        self.assertEqual(len(small.obstacles), 4)


class TestObstacleModeRegistry(unittest.TestCase):
    def test_mode_is_implemented_and_creates_obstacles(self):
        manager = GameModeManager()
        self.assertTrue(manager.select_mode("obstacle").implemented)
        state = manager.create_game("obstacle", width=30, height=20)
        self.assertEqual(state.mode, "obstacle")
        self.assertTrue(state.obstacles)


if __name__ == "__main__":
    unittest.main()
