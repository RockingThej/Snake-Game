"""Score Manager persistence tests for two-player battle results."""
import tempfile
import unittest
from pathlib import Path

from db import create_user, get_scores_for_user
from engine.two_player_game_state import TwoPlayerGameState
from scoring import ScoreManager


class TestScoreManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(
            dir=Path(__file__).resolve().parent, prefix=".tmp-score-"
        )
        self.addCleanup(self.temp_dir.cleanup)
        self.db_path = Path(self.temp_dir.name) / "snake.sqlite3"
        self.player1 = create_user("PlayerOne", "hash-one", self.db_path)
        self.player2 = create_user("PlayerTwo", "hash-two", self.db_path)
        self.state = TwoPlayerGameState(
            width=18,
            height=10,
            player_ids={
                "player1": self.player1,
                "player2": self.player2,
            },
        )
        self.state.scores.update({"player1": 30, "player2": 20})
        self.manager = ScoreManager(db_path=self.db_path)

    def test_saves_both_players_final_scores(self):
        saved = self.manager.save_battle_result(self.state)

        self.assertEqual(set(saved), {"player1", "player2"})
        self.assertEqual(
            get_scores_for_user(self.player1, db_path=self.db_path)[0]["score"],
            30,
        )
        self.assertEqual(
            get_scores_for_user(self.player2, db_path=self.db_path)[0]["score"],
            20,
        )
        self.assertEqual(
            get_scores_for_user(self.player1, db_path=self.db_path)[0]["mode"],
            "two_player_battle",
        )

    def test_requires_both_player_accounts_before_saving(self):
        self.state.player_ids = {"player1": self.player1}

        with self.assertRaisesRegex(ValueError, "player2 must be signed in"):
            self.manager.save_battle_result(self.state)

        self.assertEqual(
            get_scores_for_user(self.player1, db_path=self.db_path), []
        )

    def test_unknown_player_account_does_not_partially_save(self):
        self.state.player_ids["player2"] = 99999

        with self.assertRaisesRegex(ValueError, "player2 account does not exist"):
            self.manager.save_battle_result(self.state)

        self.assertEqual(
            get_scores_for_user(self.player1, db_path=self.db_path), []
        )


if __name__ == "__main__":
    unittest.main()
