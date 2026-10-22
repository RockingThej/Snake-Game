"""Unit tests for the engine: TC-MOVE-001, TC-FOOD-001/002, TC-COLLISION-001, TC-CLASSIC-001."""
import random
import unittest

from engine import collision
from engine.collision import Collision
from engine.food import spawn_food
from engine.game_state import GameState, Status
from engine.snake import Direction, Snake


class TestSnakeMovement(unittest.TestCase):
    def test_moves_one_cell_per_tick(self):
        s = Snake((5, 5), Direction.RIGHT, length=3)
        s.move()
        self.assertEqual(s.head, (6, 5))
        self.assertEqual(len(s), 3)

    def test_direction_change(self):
        s = Snake((5, 5), Direction.RIGHT)
        s.set_direction(Direction.UP)
        s.move()
        self.assertEqual(s.head, (5, 4))

    def test_reverse_is_ignored(self):
        s = Snake((5, 5), Direction.RIGHT)
        s.set_direction(Direction.LEFT)
        s.move()
        self.assertEqual(s.head, (6, 5))

    def test_two_quick_turns_cannot_reverse(self):
        s = Snake((5, 5), Direction.RIGHT)
        s.set_direction(Direction.UP)
        s.set_direction(Direction.LEFT)   # reversal of RIGHT: must be ignored
        s.move()
        self.assertNotEqual(s.head, (4, 5))

    def test_grow_increases_length(self):
        s = Snake((5, 5), Direction.RIGHT, length=3)
        s.grow()
        s.move()
        self.assertEqual(len(s), 4)


class TestFood(unittest.TestCase):
    def test_food_never_on_occupied_cell(self):
        occupied = {(x, y) for x in range(5) for y in range(5)} - {(2, 3)}
        self.assertEqual(spawn_food(5, 5, occupied, random.Random(1)), (2, 3))

    def test_full_board_returns_none(self):
        occupied = {(x, y) for x in range(3) for y in range(3)}
        self.assertIsNone(spawn_food(3, 3, occupied))


class TestCollision(unittest.TestCase):
    def test_wall(self):
        s = Snake((0, 0), Direction.LEFT, length=1)
        s.move()
        self.assertEqual(collision.check(s, 10, 10), Collision.WALL)

    def test_self(self):
        s = Snake((5, 5), Direction.RIGHT, length=5)
        for turn in (Direction.DOWN, Direction.LEFT, Direction.UP):
            s.set_direction(turn)
            s.move()
        self.assertEqual(collision.check(s, 20, 20), Collision.SELF)

    def test_obstacle(self):
        s = Snake((5, 5), Direction.RIGHT, length=1)
        s.move()
        self.assertEqual(collision.check(s, 10, 10, {(6, 5)}), Collision.OBSTACLE)

    def test_no_collision(self):
        s = Snake((5, 5), Direction.RIGHT)
        s.move()
        self.assertIsNone(collision.check(s, 10, 10))


class TestClassicGame(unittest.TestCase):
    def make(self):
        g = GameState(width=10, height=10, rng=random.Random(0))
        g.start()
        return g

    def test_tick_does_nothing_before_start(self):
        g = GameState(rng=random.Random(0))
        before = g.snake.head
        g.tick()
        self.assertEqual(g.snake.head, before)

    def test_eating_food_grows_and_scores(self):
        g = self.make()
        hx, hy = g.snake.head
        g.food = (hx + 1, hy)
        g.tick()
        self.assertEqual(g.score, GameState.POINTS_PER_FOOD)
        g.tick()
        self.assertEqual(len(g.snake), 4)
        self.assertNotIn(g.food, g.snake.cells())

    def test_wall_ends_game(self):
        g = self.make()
        for _ in range(20):
            g.tick()
        self.assertEqual(g.status, Status.GAME_OVER)
        self.assertEqual(g.collision, Collision.WALL)

    def test_no_movement_after_game_over(self):
        g = self.make()
        for _ in range(20):
            g.tick()
        head = g.snake.head
        g.tick()
        self.assertEqual(g.snake.head, head)


if __name__ == "__main__":
    unittest.main()
