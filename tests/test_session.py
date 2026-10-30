"""Tests for the player session and score saving (no Pygame needed)."""
import os
import shutil
import tempfile
import unittest

from auth import DbAuth
from engine.game_state import GameState
from ui.session import Session


class TestSession(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.db = os.path.join(self.tmp, "session.sqlite3")
        self.session = Session(db_path=self.db)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def finished_state(self, score):
        state = GameState(width=10, height=10)
        state.score = score
        return state

    def test_not_logged_in_saves_nothing(self):
        self.assertIsNone(self.session.save_result(self.finished_state(30)))
        self.assertEqual(self.session.leaderboard(), [])

    def test_login_then_finish_game_saves_to_leaderboard(self):
        DbAuth(db_path=self.db).register("alice", "secret123")
        self.session.login("alice")
        self.assertTrue(self.session.logged_in)

        self.assertTrue(self.session.finish_game(self.finished_state(50)))

        board = self.session.leaderboard()
        self.assertEqual(board[0]["username"], "alice")
        self.assertEqual(board[0]["score"], 50)

    def test_game_over_callback_receives_saved_flag(self):
        calls = []
        self.session.on_game_over = lambda state, saved: calls.append(saved)
        self.session.finish_game(self.finished_state(10))
        self.assertEqual(calls, [False])

    def test_logout_clears_user(self):
        DbAuth(db_path=self.db).register("bob", "secret123")
        self.session.login("bob")
        self.session.logout()
        self.assertFalse(self.session.logged_in)

    def test_login_unknown_user_raises(self):
        with self.assertRaises(ValueError):
            self.session.login("nobody")


if __name__ == "__main__":
    unittest.main()
