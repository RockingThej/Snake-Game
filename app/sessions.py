"""S2-13: server-side sessions for the Flask API (SNAKE-SR-005).

The browser cookie only carries a random session id. Whether that id is
still valid is decided here, on the server, so logging out (or a timeout)
makes a copied cookie worthless. The rules come from
``auth.session_policy``, the same module the desktop game uses.
"""
import time
from contextlib import suppress

from flask import current_app

from auth import session_policy as rules

from .db import get_db


def _now():
    clock = current_app.config.get("SESSION_CLOCK") or time.time
    return clock()


def policy():
    cfg = current_app.config
    return rules.SessionPolicy(
        idle_timeout=cfg.get("SESSION_IDLE_SECONDS", 30 * 60),
        absolute_timeout=cfg.get("SESSION_ABSOLUTE_SECONDS", 8 * 60 * 60),
    )


def start(user_id):
    """Create a session for ``user_id`` and return the token for the cookie."""
    token = rules.new_token()
    now = _now()
    db = get_db()
    db.execute(
        "INSERT INTO sessions "
        "(token_hash, user_id, created_at, last_seen_at, expires_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (rules.hash_token(token), user_id, now,
         now, now + policy().absolute_timeout),
    )
    db.commit()
    return token


def load_user(token):
    """Return the user dict for a live session, else ``None``.

    A live session counts as activity. An expired one is ended on the spot.
    """
    if not isinstance(token, str) or not token:
        return None
    token_hash = rules.hash_token(token)
    db = get_db()
    row = db.execute(
        "SELECT user_id, last_seen_at, expires_at, ended_at "
        "FROM sessions WHERE token_hash = ?", (token_hash,),
    ).fetchone()
    if row is None:
        return None

    now = _now()
    reason = rules.end_reason(
        last_seen_at=row["last_seen_at"], expires_at=row["expires_at"],
        ended_at=row["ended_at"], now=now, policy=policy(),
    )
    if reason is not None:
        if reason != rules.LOGOUT:
            _end(token_hash, now, reason)
        return None

    user = db.execute(
        "SELECT id, username, email FROM users WHERE id = ?",
        (row["user_id"],),
    ).fetchone()
    if user is None:
        return None
    db.execute("UPDATE sessions SET last_seen_at = ? WHERE token_hash = ?",
               (now, token_hash))
    db.commit()
    return dict(user)


def _end(token_hash, now, reason):
    db = get_db()
    db.execute(
        "UPDATE sessions SET ended_at = ?, end_reason = ? "
        "WHERE token_hash = ? AND ended_at IS NULL",
        (now, reason, token_hash),
    )
    db.commit()


def end(token, reason=rules.LOGOUT):
    """Log one session out. Unknown or missing tokens are ignored."""
    with suppress(ValueError):
        _end(rules.hash_token(token), _now(), reason)


def end_all(user_id, reason=rules.LOGOUT_ALL):
    """Log a user out of every session. Return how many were ended."""
    db = get_db()
    cur = db.execute(
        "UPDATE sessions SET ended_at = ?, end_reason = ? "
        "WHERE user_id = ? AND ended_at IS NULL",
        (_now(), reason, user_id),
    )
    db.commit()
    return cur.rowcount
