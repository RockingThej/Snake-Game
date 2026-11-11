"""S2-13: Logout and session termination (SNAKE-F-004, SNAKE-SR-005).

A login creates a server-side session identified by a random token. The
session ends on logout, after the idle timeout, or at the absolute limit;
after that the token is useless even if somebody kept a copy.
"""
import time
from dataclasses import dataclass

from auth import session_policy as policy_rules
from auth.session_policy import DEFAULT_POLICY, SessionPolicy
from db.auth_session_repository import (
    count_active_auth_sessions,
    create_auth_session,
    end_all_auth_sessions,
    end_auth_session,
    get_auth_session,
    purge_auth_sessions,
    touch_auth_session,
)
from db.user_repository import get_user_by_id


class SessionError(Exception):
    """Base class: the presented session cannot be used."""

    reason = "invalid"


class SessionNotFoundError(SessionError):
    """The token does not belong to any session."""

    reason = "not_found"


class SessionEndedError(SessionError):
    """The player logged out (or the session was terminated)."""

    reason = policy_rules.LOGOUT


class SessionExpiredError(SessionError):
    """The idle or absolute time limit was reached."""

    def __init__(self, reason):
        super().__init__("session ended: %s" % reason)
        self.reason = reason


@dataclass(frozen=True)
class SessionInfo:
    user_id: int
    username: str
    created_at: float
    last_seen_at: float
    expires_at: float


class SessionManager:
    """Create, validate and terminate login sessions.

    ``clock`` is injectable so tests can move time without sleeping.
    """

    def __init__(self, db_path=None, policy=None, clock=time.time):
        self.db_path = db_path
        self.policy = policy or DEFAULT_POLICY
        if not isinstance(self.policy, SessionPolicy):
            raise TypeError("policy must be a SessionPolicy")
        self._clock = clock

    def start(self, user_id):
        """Begin a session for an authenticated user; return its token."""
        token = policy_rules.new_token()
        now = self._clock()
        create_auth_session(
            user_id, policy_rules.hash_token(token), now,
            now + self.policy.absolute_timeout, db_path=self.db_path,
        )
        return token

    def validate(self, token, touch=True):
        """Return ``SessionInfo`` for a live session or raise SessionError.

        A successful call counts as activity and slides the idle window,
        unless ``touch`` is False.
        """
        if not isinstance(token, str) or not token:
            raise SessionNotFoundError("no session token")
        token_hash = policy_rules.hash_token(token)
        row = get_auth_session(token_hash, db_path=self.db_path)
        if row is None:
            raise SessionNotFoundError("unknown session")

        now = self._clock()
        reason = policy_rules.end_reason(
            last_seen_at=row["last_seen_at"], expires_at=row["expires_at"],
            ended_at=row["ended_at"], now=now, policy=self.policy,
        )
        if reason == policy_rules.LOGOUT:
            raise SessionEndedError("session was ended")
        if reason is not None:
            end_auth_session(token_hash, now, reason, db_path=self.db_path)
            raise SessionExpiredError(reason)

        user = get_user_by_id(row["user_id"], db_path=self.db_path)
        if user is None:
            raise SessionNotFoundError("account no longer exists")
        if touch:
            touch_auth_session(token_hash, now, db_path=self.db_path)
        return SessionInfo(
            user_id=user["id"], username=user["username"],
            created_at=row["created_at"],
            last_seen_at=now if touch else row["last_seen_at"],
            expires_at=row["expires_at"],
        )

    def is_active(self, token, touch=False):
        """True if the token is a live session. Does not slide the window."""
        try:
            self.validate(token, touch=touch)
        except SessionError:
            return False
        return True

    def end(self, token, reason=policy_rules.LOGOUT):
        """Log out one session. Safe to call twice. True if it was active."""
        if not isinstance(token, str) or not token:
            return False
        return end_auth_session(
            policy_rules.hash_token(token), self._clock(), reason,
            db_path=self.db_path,
        )

    def end_all(self, user_id, reason=policy_rules.LOGOUT_ALL):
        """Log a user out everywhere. Return the number of sessions ended."""
        return end_all_auth_sessions(
            user_id, self._clock(), reason, db_path=self.db_path
        )

    def active_count(self, user_id):
        return count_active_auth_sessions(user_id, db_path=self.db_path)

    def purge(self, keep_seconds=24 * 60 * 60):
        """Delete sessions that finished more than ``keep_seconds`` ago."""
        cutoff = self._clock() - keep_seconds
        return purge_auth_sessions(cutoff, cutoff, db_path=self.db_path)
