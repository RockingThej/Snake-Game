"""Repository functions for user records."""
import sqlite3

from db.connection import get_connection


class UserAlreadyExistsError(ValueError):
    """Raised when a username is already registered."""


def create_user(username, password_hash, db_path=None):
    """Create a user using a precomputed password hash and return its id."""
    if not isinstance(username, str) or not username.strip():
        raise ValueError("username must not be empty")
    if not isinstance(password_hash, str) or not password_hash.strip():
        raise ValueError("password_hash must not be empty")

    connection = get_connection(db_path)
    try:
        with connection:
            cursor = connection.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username.strip(), password_hash),
            )
        return cursor.lastrowid
    except sqlite3.IntegrityError as exc:
        if "users.username" in str(exc).lower():
            raise UserAlreadyExistsError(
                "username is already registered"
            ) from exc
        raise
    finally:
        connection.close()


def get_user_by_username(username, db_path=None):
    """Return a user record by username, or ``None`` when it does not exist."""
    connection = get_connection(db_path)
    try:
        row = connection.execute(
            "SELECT id, username, password_hash, created_at FROM users "
            "WHERE username = ?",
            (username,),
        ).fetchone()
        return dict(row) if row is not None else None
    finally:
        connection.close()


def get_user_by_id(user_id, db_path=None):
    """Return a user record by id, or ``None`` when it does not exist."""
    connection = get_connection(db_path)
    try:
        row = connection.execute(
            "SELECT id, username, password_hash, created_at FROM users "
            "WHERE id = ?",
            (user_id,),
        ).fetchone()
        return dict(row) if row is not None else None
    finally:
        connection.close()
