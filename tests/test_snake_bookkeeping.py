"""The snake's O(1) self-collision bookkeeping matches the plain definition."""
import random
import unittest

from engine import collision
from engine.snake import Direction, Snake


def brute_force_hits_self(snake):
    body = list(snake.body)
    return body[0] in body[1:]


class TestSnakeBookkeeping(unittest.TestCase):
    def test_cells_match_the_body_after_moves_and_growth(self):
        snake = Snake((10, 10), Direction.RIGHT, length=4)
        snake.grow(3)
        for _ in range(8):
            snake.move()
        self.assertEqual(snake.cells(), set(snake.body))
        self.assertEqual(len(snake.cells()), len(snake))

    def test_random_walks_agree_with_the_brute_force_check(self):
        directions = list(Direction)
        for seed in range(200):
            rng = random.Random(seed)
            snake = Snake((15, 15), rng.choice(directions),
                          length=rng.randint(1, 12))
            for _ in range(60):
                snake.set_direction(rng.choice(directions))
                if rng.random() < 0.3:
                    snake.grow()
                snake.move()
                self.assertEqual(snake.head_overlaps_body(),
                                 brute_force_hits_self(snake), seed)
                self.assertEqual(collision.hits_self(snake),
                                 brute_force_hits_self(snake), seed)
                self.assertEqual(snake.cells(), set(snake.body), seed)

    def test_moving_into_the_cell_the_tail_just_left_is_allowed(self):
        # A 2x2 loop: the head chases the tail and never collides.
        snake = Snake((5, 5), Direction.RIGHT, length=4)
        for turn in (Direction.DOWN, Direction.LEFT, Direction.UP):
            snake.set_direction(turn)
            snake.move()
            self.assertFalse(snake.head_overlaps_body())

    def test_growing_snake_does_not_free_the_tail_cell(self):
        snake = Snake((5, 5), Direction.RIGHT, length=4)
        tail = snake.body[-1]
        snake.grow()
        snake.move()
        self.assertIn(tail, snake.cells())


if __name__ == "__main__":
    unittest.main()
