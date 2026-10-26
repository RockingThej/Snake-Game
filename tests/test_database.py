"""Repository and first-run schema tests (TC-SCORE-002)."""
import tempfile
import unittest
from pathlib import Path
import sqlite3

from db import (
    UserAlreadyExistsError,
    create_user,
    get_leaderboard,
    get_scores_for_user,
    get_table_names,
    get_user_by_id,
    get_user_by_username,
    initialize_database,
    save_score,
)


class TestDatabaseSchema(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(
            dir=Path(__file__).resolve().parent, prefix=".tmp-db-"
        )
        self.addCleanup(self.temp_dir.cleanup)
        self.db_path = Path(self.temp_dir.name) / "snake.sqlite3"

    def test_first_run_creates_required_tables_and_is_idempotent(self):
        initialize_database(self.db_path)
        initialize_database(self.db_path)

        self.assertTrue(self.db_path.is_file())
        self.assertEqual(
            get_table_names(self.db_path),
            ("users", "scores", "leaderboard"),
        )


class TestRepositories(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(
            dir=Path(__file__).resolve().parent, prefix=".tmp-db-"
        )
        self.addCleanup(self.temp_dir.cleanup)
        self.db_path = Path(self.temp_dir.name) / "snake.sqlite3"
        self.alice = create_user("Alice", "hash-alice", self.db_path)
        self.bob = create_user("Bob", "hash-bob", self.db_path)

    def test_create_and_find_users(self):
        self.assertEqual(get_user_by_username("alice", self.db_path)["id"],
                         self.alice)
        self.assertEqual(get_user_by_id(self.bob, self.db_path)["username"],
                         "Bob")
        self.assertIsNone(get_user_by_username("missing", self.db_path))

    def test_duplicate_usernames_are_rejected_case_insensitively(self):
        with self.assertRaises(UserAlreadyExistsError):
            create_user("ALICE", "another-hash", self.db_path)

    def test_score_history_and_personal_best_are_persisted(self):
        low_score_id = save_score(
            self.alice, 25, "classic", "easy", self.db_path
        )
        best_score_id = save_score(
            self.alice, 70, "survival", "hard", self.db_path
        )
        tied_score_id = save_score(
            self.alice, 70, "classic", "medium", self.db_path
        )

        scores = get_scores_for_user(self.alice, db_path=self.db_path)
        self.assertEqual(len(scores), 3)
        self.assertEqual({row["id"] for row in scores},
                         {low_score_id, best_score_id, tied_score_id})
        self.assertEqual(scores[0]["score"], 70)

        board = get_leaderboard(db_path=self.db_path)
        alice_entry = next(
            row for row in board if row["user_id"] == self.alice
        )
        self.assertEqual(alice_entry["score"], 70)
        self.assertEqual(alice_entry["mode"], "survival")
        self.assertEqual(alice_entry["difficulty"], "hard")

    def test_leaderboard_ranks_each_users_best_score(self):
        save_score(self.alice, 30, "classic", "easy", self.db_path)
        save_score(self.bob, 90, "classic", "hard", self.db_path)

        board = get_leaderboard(db_path=self.db_path)
        self.assertEqual(
            [entry["username"] for entry in board], ["Bob", "Alice"]
        )
        self.assertEqual([entry["score"] for entry in board], [90, 30])

    def test_invalid_score_inputs_are_rejected(self):
        for invalid_score in (-1, 1.5, True):
            with self.subTest(score=invalid_score):
                with self.assertRaises(ValueError):
                    save_score(self.alice, invalid_score, "classic", "easy",
                               self.db_path)
        with self.assertRaises(ValueError):
            save_score(self.alice, 10, "", "easy", self.db_path)
        with self.assertRaises(ValueError):
            save_score(self.alice, 10, "classic", "", self.db_path)

    def test_score_for_unknown_user_is_not_saved(self):
        with self.assertRaises(sqlite3.IntegrityError):
            save_score(99999, 10, "classic", "easy", self.db_path)
        self.assertEqual(get_leaderboard(db_path=self.db_path), [])


if __name__ == "__main__":
    unittest.main()
