"""Tests for pausing and resuming gameplay (TC-GAME-002)."""
import unittest

from engine.game_state import GameState, Status


class TestPauseResume(unittest.TestCase):
    def setUp(self):
        self.state = GameState(width=20, height=20)
        self.state.start()

    def test_pause_freezes_gameplay(self):
        head_before_pause = self.state.snake.head

        self.assertTrue(self.state.pause())
        self.assertEqual(self.state.status, Status.PAUSED)
        for _ in range(5):
            self.state.tick()

        self.assertEqual(self.state.snake.head, head_before_pause)

    def test_resume_continues_the_same_game(self):
        original_snake = self.state.snake
        head_before_pause = self.state.snake.head
        self.state.pause()

        self.assertTrue(self.state.resume())
        self.assertEqual(self.state.status, Status.RUNNING)
        self.state.tick()

        self.assertIs(self.state.snake, original_snake)
        self.assertNotEqual(self.state.snake.head, head_before_pause)

    def test_pause_and_resume_only_change_valid_states(self):
        self.assertFalse(self.state.resume())
        self.assertTrue(self.state.pause())
        self.assertFalse(self.state.pause())
        self.assertTrue(self.state.resume())

    def test_direction_input_is_ignored_while_paused(self):
        from engine.snake import Direction

        self.state.pause()
        direction_before_pause = self.state.snake.direction
        self.state.set_direction(Direction.UP)

        self.assertEqual(self.state.snake.direction, direction_before_pause)


if __name__ == "__main__":
    unittest.main()
