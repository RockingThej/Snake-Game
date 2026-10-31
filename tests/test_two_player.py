"""Two-player battle state tests (TC-MULTI-001)."""
import random
import unittest

from engine.collision import Collision
from engine.game_state import Status
from engine.snake import Direction, Snake
from engine.two_player_game_state import TwoPlayerGameState


class TestTwoPlayerGameState(unittest.TestCase):
    def make(self, **overrides):
        options = {"width": 18, "height": 10, "rng": random.Random(0)}
        options.update(overrides)
        state = TwoPlayerGameState(**options)
        state.start()
        return state

    def test_both_snakes_move_independently(self):
        state = self.make()
        state.set_direction(Direction.UP, "player1")
        state.set_direction(Direction.DOWN, "player2")

        state.tick()

        self.assertEqual(state.snakes["player1"].head, (6, 4))
        self.assertEqual(state.snakes["player2"].head, (12, 6))

    def test_food_scores_and_grows_only_the_snake_that_eats_it(self):
        state = self.make()
        state.food = (7, 5)

        state.tick()

        self.assertEqual(state.scores, {"player1": 10, "player2": 0})
        self.assertEqual(len(state.snakes["player1"]), 3)
        self.assertEqual(len(state.snakes["player2"]), 3)

        state.tick()
        self.assertEqual(len(state.snakes["player1"]), 4)
        self.assertEqual(len(state.snakes["player2"]), 3)

    def test_player_two_can_collect_food_and_score_independently(self):
        state = self.make()
        state.food = (11, 5)

        state.tick()

        self.assertEqual(state.scores, {"player1": 0, "player2": 10})
        self.assertEqual(state.score, 10)

    def test_food_spawns_outside_both_snakes(self):
        state = TwoPlayerGameState(width=18, height=10, rng=random.Random(0))

        self.assertNotIn(state.food, state.snakes["player1"].cells())
        self.assertNotIn(state.food, state.snakes["player2"].cells())

    def test_head_to_head_collision_ends_match_as_draw(self):
        state = self.make(width=8)

        state.tick()
        state.tick()

        self.assertEqual(state.status, Status.GAME_OVER)
        self.assertEqual(state.collision, Collision.SNAKE)
        self.assertIsNone(state.winner)

    def test_wall_collision_awards_match_to_other_player(self):
        state = self.make()
        state.snakes["player1"] = Snake((0, 0), Direction.LEFT, length=1)

        state.tick()

        self.assertEqual(state.status, Status.GAME_OVER)
        self.assertEqual(state.winner, "player2")

    def test_unknown_player_is_rejected(self):
        state = self.make()

        with self.assertRaisesRegex(ValueError, "unknown player"):
            state.set_direction(Direction.UP, "player3")


if __name__ == "__main__":
    unittest.main()
