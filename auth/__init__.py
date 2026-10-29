"""Authentication service and validator helpers."""

import bcrypt

from db.connection import get_connection
from db.user_repository import UserAlreadyExistsError, create_user, get_user_by_username


def validate_username(username):
    """Validate a username and return (ok, message)."""
    if username is None:
        return False, "Username is required"
    username = username.strip()
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    return True, ""


def validate_password(password):
    """Validate a password and return (ok, message)."""
    if password is None:
        return False, "Password is required"
    password = password.strip()
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    return True, ""


class DbAuth:
    """Small database-backed authentication service for login and registration."""

    def __init__(self, db_path=None):
        self.db_path = db_path

    def register(self, username, password):
        """Register a user if the username is valid and not already in use."""
        ok, message = validate_username(username)
        if not ok:
            raise ValueError(message)
        ok, message = validate_password(password)
        if not ok:
            raise ValueError(message)

        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        try:
            create_user(username.strip(), password_hash, db_path=self.db_path)
        except UserAlreadyExistsError as exc:
            raise ValueError("username already taken") from exc
        return True

    def login(self, username, password):
        """Return True when the supplied username/password matches a stored user."""
        row = get_user_by_username(username.strip(), db_path=self.db_path)
        if row is None:
            return False
        stored_hash = row["password_hash"]
        return bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
