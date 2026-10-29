"""Tests for the database-backed authentication service."""

import unittest

from auth import DbAuth, validate_password, validate_username


class TestDbAuth(unittest.TestCase):
    def test_validators_reject_short_values(self):
        self.assertFalse(validate_username("ab")[0])
        self.assertFalse(validate_password("12345")[0])

    def test_register_and_login_round_trip(self):
        auth = DbAuth(db_path="/tmp/test_snake_game_auth.sqlite3")

        self.assertTrue(auth.register("alice", "secret123"))
        self.assertTrue(auth.login("alice", "secret123"))
        self.assertFalse(auth.login("alice", "wrongpass"))


if __name__ == "__main__":
    unittest.main()
