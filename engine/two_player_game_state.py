"""Local two-player Snake game state (SNAKE-F-016 / TC-MULTI-001)."""
import random

from engine import collision
from engine.game_state import Status
from engine.food import spawn_food
from engine.snake import Direction, Snake
from modes.difficulty import DifficultyManager


class TwoPlayerGameState:
    """Two independent snakes, scores and keyboard-controlled directions.

    Both snakes advance once per tick. Food is shared on the board; whichever
    snake reaches it receives the points and growth. A wall, self, or opponent
    collision ends the match and records the surviving player as the winner.
    """

    POINTS_PER_FOOD = 10
    PLAYERS = ("player1", "player2")

    def __init__(self, width=30, height=20, mode="two_player_battle",
                 difficulty="medium", rng=None, difficulty_manager=None,
                 player_ids=None):
        if width < 8 or height < 1:
            raise ValueError("two-player board must be at least 8 cells wide")
        self.width = width
        self.height = height
        self.mode = mode
        self.difficulty_manager = difficulty_manager or DifficultyManager()
        self.difficulty = self.difficulty_manager.normalize(difficulty)
        self.tick_interval_ms = self.difficulty_manager.get_speed_ms(
            self.difficulty
        )
        self.rng = rng or random.Random()
        first_x = width // 3
        second_x = (2 * width) // 3
        middle_y = height // 2
        self.snakes = {
            "player1": Snake((first_x, middle_y), Direction.RIGHT),
            "player2": Snake((second_x, middle_y), Direction.LEFT),
        }
        self.obstacles = set()
        self.scores = {player: 0 for player in self.PLAYERS}
        self.player_ids = dict(player_ids or {})
        self.result_score_ids = None
        self.status = Status.READY
        self.collisions = {}
        self.collision = None
        self.winner = None
        self.food = spawn_food(width, height, self._occupied(), self.rng)

    @property
    def score(self):
        """Combined score for screens that expect a single score value."""
        return sum(self.scores.values())

    def _occupied(self):
        occupied = set(self.obstacles)
        for snake in self.snakes.values():
            occupied.update(snake.cells())
        return occupied

    def start(self):
        if self.status == Status.READY:
            self.status = Status.RUNNING

    def pause(self):
        if self.status != Status.RUNNING:
            return False
        self.status = Status.PAUSED
        return True

    def resume(self):
        if self.status != Status.PAUSED:
            return False
        self.status = Status.RUNNING
        return True

    def set_difficulty(self, difficulty):
        if self.status != Status.READY:
            raise RuntimeError(
                "difficulty can only be changed before the game starts"
            )
        self.difficulty = self.difficulty_manager.normalize(difficulty)
        self.tick_interval_ms = self.difficulty_manager.get_speed_ms(
            self.difficulty
        )

    def set_direction(self, direction, player_id="player1"):
        if player_id not in self.snakes:
            raise ValueError(f"unknown player: {player_id!r}")
        if self.status == Status.RUNNING:
            self.snakes[player_id].set_direction(direction)

    def tick(self):
        """Advance both snakes simultaneously by one grid cell."""
        if self.status != Status.RUNNING:
            return

        for snake in self.snakes.values():
            snake.move()

        self.collisions = {
            player: collision.check(
                snake, self.width, self.height, self.obstacles,
                other_snakes=(other for other_id, other in self.snakes.items()
                              if other_id != player),
            )
            for player, snake in self.snakes.items()
        }
        collided = [p for p, hit in self.collisions.items() if hit is not None]
        if collided:
            self.status = Status.GAME_OVER
            self.collision = self.collisions[collided[0]]
            self.winner = (
                next(p for p in self.PLAYERS if p not in collided)
                if len(collided) == 1 else None
            )
            return

        for player, snake in self.snakes.items():
            if snake.head == self.food:
                snake.grow()
                self.scores[player] += self.POINTS_PER_FOOD
                self.food = spawn_food(
                    self.width, self.height, self._occupied(), self.rng
                )
                if self.food is None:
                    self.status = Status.GAME_OVER
                    self.winner = max(
                        self.PLAYERS, key=self.scores.get
                    ) if len(set(self.scores.values())) > 1 else None
                break
