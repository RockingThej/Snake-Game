"""Game state for one single-player session (SNAKE-F-005, F-010, F-018).

Pure logic with no Pygame imports, so the UI only has to draw this object
and the whole thing can be unit tested.

Public interface other modules code against:
    GameState(width, height, mode, difficulty, rng)
    state.start()
    state.set_direction(Direction.UP)
    state.tick()
    state.snake, state.food, state.obstacles, state.score, state.status,
    state.collision (why the game ended), state.mode, state.difficulty
"""
import random
from enum import Enum

from engine import collision
from engine.food import spawn_food
from engine.snake import Direction, Snake
from modes.difficulty import DifficultyManager


class Status(Enum):
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    GAME_OVER = "game_over"


class GameState:
    POINTS_PER_FOOD = 10     # placeholder; Score Manager (S1-17) owns the rules

    def __init__(self, width=30, height=20, mode="classic",
                 difficulty="medium", rng=None, difficulty_manager=None):
        self.width = width
        self.height = height
        self.mode = mode
        self.difficulty_manager = difficulty_manager or DifficultyManager()
        self.difficulty = self.difficulty_manager.normalize(difficulty)
        self.tick_interval_ms = self.difficulty_manager.get_speed_ms(
            self.difficulty
        )
        self.rng = rng or random.Random()
        self.snake = Snake(start=(width // 2, height // 2),
                           direction=Direction.RIGHT, length=3)
        self.obstacles = set()   # filled by Obstacle Mode later
        self.score = 0
        self.status = Status.READY
        self.collision = None
        self.food = spawn_food(width, height, self._occupied(), self.rng)

    def _occupied(self):
        return self.snake.cells() | self.obstacles

    def start(self):
        if self.status == Status.READY:
            self.status = Status.RUNNING

    def pause(self):
        """Pause a running game. Return whether the state changed."""
        if self.status != Status.RUNNING:
            return False
        self.status = Status.PAUSED
        return True

    def resume(self):
        """Resume a paused game. Return whether the state changed."""
        if self.status != Status.PAUSED:
            return False
        self.status = Status.RUNNING
        return True

    def set_difficulty(self, difficulty):
        """Select a speed level before starting the game session."""
        if self.status != Status.READY:
            raise RuntimeError(
                "difficulty can only be changed before the game starts"
            )
        normalized = self.difficulty_manager.normalize(difficulty)
        self.difficulty = normalized
        self.tick_interval_ms = self.difficulty_manager.get_speed_ms(
            normalized
        )

    def set_direction(self, direction):
        if self.status == Status.RUNNING:
            self.snake.set_direction(direction)

    def tick(self):
        """Advance the game by one step. Call at the configured game speed."""
        if self.status != Status.RUNNING:
            return
        self.snake.move()

        hit = collision.check(
            self.snake, self.width, self.height, self.obstacles
        )
        if hit is not None:
            self.collision = hit
            self.status = Status.GAME_OVER
            return

        if self.snake.head == self.food:
            self.snake.grow()
            self.score += self.POINTS_PER_FOOD
            self.food = spawn_food(self.width, self.height,
                                   self._occupied(), self.rng)
            if self.food is None:        # board completely full: player wins
                self.status = Status.GAME_OVER
