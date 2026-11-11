"""Tests for configurable, player-specific keyboard input."""
import unittest

from engine.game_state import Status
from engine.snake import Direction
from engine.two_player_game_state import TwoPlayerGameState
from ui.input_handler import InputHandler


class TestInputHandler(unittest.TestCase):
    def test_resolves_configured_key_to_player_and_direction(self):
        handler = InputHandler({
            "player1": {"w": Direction.UP},
            "player2": {"up": Direction.UP},
        })

        self.assertEqual(handler.resolve("w"), ("player1", Direction.UP))
        self.assertEqual(handler.resolve("up"), ("player2", Direction.UP))

    def test_unmapped_key_returns_none(self):
        handler = InputHandler({"player1": {"w": Direction.UP}})

        self.assertIsNone(handler.resolve("x"))

    def test_rejects_empty_key_maps(self):
        with self.assertRaises(ValueError):
            InputHandler({})

    def test_dual_layout_routes_each_players_keys_to_their_own_snake(self):
        handler = InputHandler({
            "player1": {"w": Direction.UP, "s": Direction.DOWN,
                        "a": Direction.LEFT, "d": Direction.RIGHT},
            "player2": {"up": Direction.UP, "down": Direction.DOWN,
                        "left": Direction.LEFT, "right": Direction.RIGHT},
        })
        state = TwoPlayerGameState(width=18, height=10)
        state.start()

        for key in ("w", "down"):
            player_id, direction = handler.resolve(key)
            state.set_direction(direction, player_id)

        state.tick()

        self.assertEqual(state.snakes["player1"].direction, Direction.UP)
        self.assertEqual(state.snakes["player2"].direction, Direction.DOWN)
        self.assertEqual(state.status, Status.RUNNING)


if __name__ == "__main__":
    unittest.main()
