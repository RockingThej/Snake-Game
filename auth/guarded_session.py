"""S2-13: a drop-in replacement for ``ui.session.Session``.

``Session`` only remembers who is playing. ``GuardedSession`` additionally
ties that to a server-side session, so:

* logging out really ends the session (SNAKE-F-004),
* an idle or too-old session stops counting as logged in, and nothing is
  saved for it (SNAKE-SR-005),
* protected code can call ``require_login()``.

``main.build_app`` uses it. The desktop policy is more relaxed than the
web default (``DESKTOP_POLICY``) because one Survival game can last a long
time; ``touch()`` restarts the idle timer.
"""
from auth.secure_auth import SecureAuth
from auth.session_manager import SessionError, SessionManager
from auth.session_policy import SessionPolicy
from scoring.integrity import InvalidScoreError, submit_score
from ui.session import Session


# Idle for 2 hours or logged in for 12 hours ends a desktop session.
DESKTOP_POLICY = SessionPolicy(idle_timeout=2 * 60 * 60,
                               absolute_timeout=12 * 60 * 60)


class NotAuthenticatedError(PermissionError):
    """Raised when protected functionality is used without a live session."""


class GuardedSession(Session):
    def __init__(self, auth=None, db_path=None, on_game_over=None,
                 manager=None, policy=None):
        # SecureAuth also refuses accounts an administrator disabled.
        super().__init__(auth=auth or SecureAuth(db_path=db_path),
                         db_path=db_path, on_game_over=on_game_over)
        self.manager = manager or SessionManager(
            db_path, policy=policy or DESKTOP_POLICY)
        self.token = None

    # -- state -----------------------------------------------------------
    @property
    def logged_in(self):
        """True only while the underlying server-side session is live."""
        if self.token is None or self.user_id is None:
            return False
        try:
            info = self.manager.validate(self.token)
        except SessionError:
            self._forget()
            return False
        return info.user_id == self.user_id

    def save_result(self, state):
        """Store a finished game through the integrity checks (S2-16).

        Returns the score id, or ``None`` when nobody is logged in or the
        result is not acceptable (nothing is stored in that case).
        """
        if not self.logged_in:
            return None
        try:
            return submit_score(
                self.user_id, state.score, state.mode, state.difficulty,
                actor_id=self.user_id, db_path=self.db_path)
        except InvalidScoreError:
            return None

    def require_login(self):
        """Return the user id, or raise NotAuthenticatedError."""
        if not self.logged_in:
            raise NotAuthenticatedError("login required")
        return self.user_id

    def touch(self):
        """Count activity (e.g. a key press) so the idle timer restarts."""
        return self.logged_in

    # -- transitions -----------------------------------------------------
    def login(self, username):
        user_id = super().login(username)
        if self.token is not None:       # logging in again: drop the old one
            self.manager.end(self.token)
        self.token = self.manager.start(user_id)
        return user_id

    def logout(self):
        if self.token is not None:
            self.manager.end(self.token)
        self._forget()

    def logout_everywhere(self):
        """End every session of this account (all devices/windows)."""
        user_id = self.user_id
        if user_id is not None:
            self.manager.end_all(user_id)
        self._forget()

    def _forget(self):
        self.token = None
        super().logout()
