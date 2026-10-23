"""Tests for configurable, player-specific keyboard input."""
import unittest

from engine.snake import Direction
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


if __name__ == "__main__":
    unittest.main()
