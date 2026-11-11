"""S2-14 / S2-17: login and registration with extra safeguards.

* Accounts an administrator has disabled cannot log in (S2-14).
* Input limits that ``DbAuth`` lacks (S2-17, SNAKE-SR-003): bounded
  usernames without control characters, and passwords within bcrypt's
  72-byte limit. Without this, typing a 73+ character password on the login
  screen raised an unhandled ``ValueError`` from bcrypt.
"""
import re

from auth import DbAuth
from db import get_user_by_username
from db.admin_repository import is_account_disabled

USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{3,32}$")
MAX_PASSWORD_BYTES = 72          # bcrypt ignores or rejects anything longer


def _too_long(password):
    return len(password.encode("utf-8")) > MAX_PASSWORD_BYTES


class SecureAuth(DbAuth):
    """``DbAuth`` plus the account-status check and input limits.

    The login screen shows the same "wrong username or password" message for
    a disabled account as for a wrong password, so it reveals nothing.
    """

    def register(self, username, password):
        if not isinstance(username, str) or not isinstance(password, str):
            raise ValueError("Username and password are required")
        if not USERNAME_PATTERN.match(username.strip()):
            raise ValueError(
                "Username must be 3-32 characters: letters, numbers, "
                "dot, dash or underscore")
        if _too_long(password):
            raise ValueError(
                "Password must be at most %d bytes" % MAX_PASSWORD_BYTES)
        return super().register(username, password)

    def login(self, username, password):
        if not isinstance(username, str) or not isinstance(password, str):
            return False
        if _too_long(password):
            return False
        user = get_user_by_username(username.strip(), db_path=self.db_path)
        if user is not None and is_account_disabled(
                user["id"], db_path=self.db_path):
            return False
        return super().login(username, password)
