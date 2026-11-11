"""Engine integration tests (S2-04): whole games, all modes, plus saving.

A small pathfinding bot plays seeded games tick by tick. After every tick the
board is checked for impossible states, so a bug in movement, food, collision
or the mode rules shows up even if no single unit test covers that exact case.
"""
import os
import random
import shutil
import tempfile
import unittest
from collections import deque

from db import create_user
from engine.collision import Collision
from engine.game_state import GameState, Status
from engine.snake import Direction
from modes import GameModeManager
from modes.rules import SurvivalRules
from ui.session import Session

MODES = ("classic", "obstacle", "survival")


def next_direction(game):
    """Direction of the first step on a shortest safe path to the food."""
    blocked = set(game.obstacles)
    blocked.update(list(game.snake.body)[:-1])      # the tail moves away
    start, goal = game.snake.head, game.food
    came_from = {start: None}
    queue = deque([start])
    while queue:
        cell = queue.popleft()
        if cell == goal:
            break
        for direction in Direction:
            dx, dy = direction.value
            nxt = (cell[0] + dx, cell[1] + dy)
            if (0 <= nxt[0] < game.width and 0 <= nxt[1] < game.height
                    and nxt not in blocked and nxt not in came_from):
                came_from[nxt] = (cell, direction)
                queue.append(nxt)
    if goal not in came_from:
        return None
    cell = goal
    while came_from[cell][0] != start:
        cell = came_from[cell][0]
    return came_from[cell][1]


def check_invariants(test, game):
    head_x, head_y = game.snake.head
    if game.status == Status.RUNNING:
        test.assertTrue(0 <= head_x < game.width and 0 <= head_y < game.height)
        # no two segments share a cell
        test.assertEqual(len(game.snake.cells()), len(game.snake))
        test.assertFalse(game.snake.cells() & game.obstacles)
    if game.food is not None:
        test.assertNotIn(game.food, game.snake.cells())
        test.assertNotIn(game.food, game.obstacles)
    test.assertEqual(game.score, game.foods_eaten * GameState.POINTS_PER_FOOD)
    # growth is applied on the move after eating, so length trails by at most 1
    test.assertIn(len(game.snake) - 3 - game.foods_eaten, (0, -1))


def play(test, mode, seed, ticks=600):
    game = GameState(mode=mode, rng=random.Random(seed))
    game.start()
    last_interval, last_level = game.tick_interval_ms, game.level
    for _ in range(ticks):
        direction = next_direction(game)
        if direction is not None:
            game.set_direction(direction)
        game.tick()
        check_invariants(test, game)
        test.assertLessEqual(game.tick_interval_ms, last_interval)
        test.assertGreaterEqual(game.level, last_level)
        last_interval, last_level = game.tick_interval_ms, game.level
        if game.status == Status.GAME_OVER:
            break
    return game


class TestBotPlaysFullGames(unittest.TestCase):
    def test_invariants_hold_in_every_mode(self):
        for mode in MODES:
            for seed in range(4):
                with self.subTest(mode=mode, seed=seed):
                    game = play(self, mode, seed)
                    self.assertGreaterEqual(game.foods_eaten, 5)

    def test_survival_gets_harder_over_a_long_game(self):
        game = play(self, "survival", seed=1, ticks=1500)
        self.assertGreaterEqual(game.level, 3)
        self.assertLess(game.tick_interval_ms, 110)
        self.assertTrue(game.obstacles)
        self.assertGreaterEqual(game.tick_interval_ms,
                                SurvivalRules.MIN_INTERVAL_MS)

    def test_same_seed_replays_identically(self):
        for mode in MODES:
            with self.subTest(mode=mode):
                a, b = play(self, mode, 9), play(self, mode, 9)
                self.assertEqual(list(a.snake.body), list(b.snake.body))
                self.assertEqual((a.score, a.food, a.obstacles),
                                 (b.score, b.food, b.obstacles))


class TestGameFlow(unittest.TestCase):
    def test_pause_freezes_the_game_and_resume_continues_it(self):
        game = GameState(mode="obstacle", rng=random.Random(1))
        game.start()
        game.tick()
        head = game.snake.head
        self.assertTrue(game.pause())
        game.tick()
        self.assertEqual(game.snake.head, head)
        self.assertTrue(game.resume())
        game.tick()
        self.assertNotEqual(game.snake.head, head)

    def test_game_over_is_final(self):
        for mode in MODES:
            with self.subTest(mode=mode):
                game = GameState(mode=mode, rng=random.Random(0))
                game.start()
                game.obstacles = {(game.snake.head[0] + 1, game.snake.head[1])}
                game.tick()
                self.assertEqual(game.status, Status.GAME_OVER)
                score, head = game.score, game.snake.head
                game.set_direction(Direction.UP)
                game.tick()
                self.assertEqual((game.score, game.snake.head), (score, head))
                self.assertFalse(game.pause())

    def test_wall_collision_in_every_mode(self):
        for mode in MODES:
            with self.subTest(mode=mode):
                game = GameState(width=12, height=10, mode=mode,
                                 rng=random.Random(2))
                game.start()
                game.obstacles = set()
                for _ in range(20):
                    game.tick()
                self.assertEqual(game.status, Status.GAME_OVER)
                self.assertEqual(game.collision, Collision.WALL)

    def test_mode_manager_builds_every_playable_mode(self):
        manager = GameModeManager()
        for mode in manager.list_modes():
            if not mode.implemented:
                continue
            with self.subTest(mode=mode.id):
                state = manager.create_game(mode.id, width=30, height=20,
                                            difficulty="hard")
                self.assertEqual((state.mode, state.difficulty),
                                 (mode.id, "hard"))
                self.assertEqual(state.status, Status.READY)


class TestEngineToDatabase(unittest.TestCase):
    """Engine result -> Session -> SQLite score and leaderboard."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.db = os.path.join(self.tmp, "integration.sqlite3")
        create_user("alice", "not-a-real-hash", db_path=self.db)
        # auth is not used here, so no password hashing library is needed
        self.session = Session(auth=object(), db_path=self.db)
        self.session.login("alice")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_finished_games_are_saved_with_their_mode(self):
        for mode in MODES:
            game = play(self, mode, seed=3, ticks=300)
            if game.status != Status.GAME_OVER:
                game.status = Status.GAME_OVER
            self.assertTrue(self.session.finish_game(game))
        board = self.session.leaderboard()
        self.assertEqual(len(board), 1)                  # one best per player
        self.assertEqual(board[0]["username"], "alice")
        self.assertGreater(board[0]["score"], 0)
        self.assertIn(board[0]["mode"], MODES)


if __name__ == "__main__":
    unittest.main()
