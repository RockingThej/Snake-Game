"""S2-13: the session-management policy (SNAKE-SR-005).

Pure logic with no database or UI imports. Both the desktop game
(``auth.session_manager``) and the Flask backend (``app.sessions``) use it,
so "when does a session end?" has exactly one definition.
"""
import hashlib
import secrets
from dataclasses import dataclass

# Reasons a session can end. Stored in the database for auditing.
LOGOUT = "logout"
LOGOUT_ALL = "logout_all"
IDLE_TIMEOUT = "idle_timeout"
EXPIRED = "expired"
ACCOUNT_CHANGED = "account_changed"


@dataclass(frozen=True)
class SessionPolicy:
    """How long a login lasts.

    idle_timeout: seconds of inactivity before the session ends.
    absolute_timeout: hard limit on a session's total lifetime, however
        active the player is.
    """

    idle_timeout: float = 30 * 60
    absolute_timeout: float = 8 * 60 * 60

    def __post_init__(self):
        for name in ("idle_timeout", "absolute_timeout"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError("%s must be a number" % name)
            if value <= 0:
                raise ValueError("%s must be positive" % name)
        if self.idle_timeout > self.absolute_timeout:
            raise ValueError("idle_timeout cannot exceed absolute_timeout")


DEFAULT_POLICY = SessionPolicy()


def new_token():
    """Return a new unguessable session token."""
    return secrets.token_urlsafe(32)


def hash_token(token):
    """Return the value stored in the database for ``token``."""
    if not isinstance(token, str) or not token:
        raise ValueError("token must be a non-empty string")
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def end_reason(*, last_seen_at, expires_at, ended_at, now, policy):
    """Return why a session is no longer usable, or ``None`` if it is.

    Order matters: an explicit logout wins over a timeout, and the absolute
    limit wins over the idle limit.
    """
    if ended_at is not None:
        return LOGOUT
    if now >= expires_at:
        return EXPIRED
    if now - last_seen_at >= policy.idle_timeout:
        return IDLE_TIMEOUT
    return None
