"""Repository functions for login sessions (S2-13).

All SQL for the ``auth_sessions`` table lives here, as the README requires.
"""
from contextlib import closing

from db.connection import get_connection


def create_auth_session(user_id, token_hash, now, expires_at, db_path=None):
    """Store a new active session and return its row id."""
    with closing(get_connection(db_path)) as connection:
        with connection:
            cursor = connection.execute(
                "INSERT INTO auth_sessions "
                "(token_hash, user_id, created_at, last_seen_at, expires_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (token_hash, user_id, now, now, expires_at),
            )
        return cursor.lastrowid


def get_auth_session(token_hash, db_path=None):
    """Return the session row for a token hash, or ``None``."""
    with closing(get_connection(db_path)) as connection:
        row = connection.execute(
            "SELECT id, token_hash, user_id, created_at, last_seen_at, "
            "expires_at, ended_at, end_reason "
            "FROM auth_sessions WHERE token_hash = ?",
            (token_hash,),
        ).fetchone()
        return dict(row) if row is not None else None


def touch_auth_session(token_hash, now, db_path=None):
    """Record activity on an active session (slides the idle window)."""
    with closing(get_connection(db_path)) as connection:
        with connection:
            connection.execute(
                "UPDATE auth_sessions SET last_seen_at = ? "
                "WHERE token_hash = ? AND ended_at IS NULL",
                (now, token_hash),
            )


def end_auth_session(token_hash, now, reason, db_path=None):
    """End one session. Return True if it was active before the call."""
    with closing(get_connection(db_path)) as connection:
        with connection:
            cursor = connection.execute(
                "UPDATE auth_sessions SET ended_at = ?, end_reason = ? "
                "WHERE token_hash = ? AND ended_at IS NULL",
                (now, reason, token_hash),
            )
        return cursor.rowcount > 0


def end_all_auth_sessions(user_id, now, reason, db_path=None):
    """End every active session of a user. Return how many were ended."""
    with closing(get_connection(db_path)) as connection:
        with connection:
            cursor = connection.execute(
                "UPDATE auth_sessions SET ended_at = ?, end_reason = ? "
                "WHERE user_id = ? AND ended_at IS NULL",
                (now, reason, user_id),
            )
        return cursor.rowcount


def count_active_auth_sessions(user_id, db_path=None):
    """Number of sessions of a user that have not been ended."""
    with closing(get_connection(db_path)) as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS n FROM auth_sessions "
            "WHERE user_id = ? AND ended_at IS NULL",
            (user_id,),
        ).fetchone()
        return row["n"]


def purge_auth_sessions(ended_before, expired_before, db_path=None):
    """Delete finished sessions to keep the table small. Return the count."""
    with closing(get_connection(db_path)) as connection:
        with connection:
            cursor = connection.execute(
                "DELETE FROM auth_sessions "
                "WHERE (ended_at IS NOT NULL AND ended_at < ?) "
                "OR expires_at < ?",
                (ended_before, expired_before),
            )
        return cursor.rowcount
