"""Tests for the database-backed authentication service."""

import os
import shutil
import tempfile
import unittest

from auth import DbAuth, validate_password, validate_username


class TestDbAuth(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmp_dir, "test_auth.sqlite3")

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_validators_reject_short_values(self):
        self.assertFalse(validate_username("ab")[0])
        self.assertFalse(validate_password("12345")[0])

    def test_register_and_login_round_trip(self):
        auth = DbAuth(db_path=self.db_path)

        self.assertTrue(auth.register("alice", "secret123"))
        self.assertTrue(auth.login("alice", "secret123"))
        self.assertFalse(auth.login("alice", "wrongpass"))


if __name__ == "__main__":
    unittest.main()