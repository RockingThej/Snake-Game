"""Administration Module (S2-14): SRS 7.2 administrator use cases.

Every public method first re-checks that the caller is (still) an
administrator (SNAKE-SR-002) and, when built from a login session, that the
session is still alive (SNAKE-SR-005). Every change is written to the audit
log. Passwords and password hashes are never returned or logged.
"""
import bcrypt

from admin import config as game_config
from auth import validate_password
from auth.session_manager import SessionManager
from auth.session_policy import ACCOUNT_CHANGED
from db import admin_repository as repo
from db import get_leaderboard, get_scores_for_user, get_user_by_id
from scoring import integrity, stats

MAX_PAGE = 200


class PermissionDeniedError(PermissionError):
    """The caller is not an authenticated administrator."""


class AdminError(ValueError):
    """The request is not allowed (for example, removing the last admin)."""


def _check_int(value, name, minimum):
    if isinstance(value, bool) or not isinstance(value, int):
        raise AdminError("%s must be an integer" % name)
    if value < minimum:
        raise AdminError("%s must be at least %d" % (name, minimum))
    return value


class AdminService:
    def __init__(self, actor_id, db_path=None, session=None):
        self.actor_id = actor_id
        self.db_path = db_path
        self._session = session
        self._sessions = SessionManager(db_path)

    @classmethod
    def from_session(cls, session):
        """Build a service bound to a ``GuardedSession``.

        Raises ``NotAuthenticatedError`` if nobody is logged in. The binding
        is re-checked on every call, so logging out locks the service again.
        """
        return cls(session.require_login(), db_path=session.db_path,
                   session=session)

    # ------------------------------------------------------ authorisation
    def _authorize(self):
        if self._session is not None:
            try:
                user_id = self._session.require_login()
            except PermissionError as exc:
                raise PermissionDeniedError("login required") from exc
            if user_id != self.actor_id:
                raise PermissionDeniedError("session belongs to someone else")
        if not repo.is_admin(self.actor_id, db_path=self.db_path):
            raise PermissionDeniedError("administrator access required")

    def _audit(self, action, target=None, detail=None):
        actor = get_user_by_id(self.actor_id, db_path=self.db_path)
        repo.add_audit_entry(
            self.actor_id, actor["username"] if actor else "?", action,
            target, detail, db_path=self.db_path)

    def _require_user(self, user_id):
        _check_int(user_id, "user_id", 1)
        user = repo.get_user(user_id, db_path=self.db_path)
        if user is None:
            raise AdminError("unknown user: %d" % user_id)
        return user

    # -------------------------------------------------------- view users
    def list_users(self, search=None, limit=50, offset=0):
        self._authorize()
        _check_int(limit, "limit", 1)
        _check_int(offset, "offset", 0)
        if search is not None and not isinstance(search, str):
            raise AdminError("search must be text")
        return repo.list_users(search=(search or "").strip() or None,
                               limit=min(limit, MAX_PAGE), offset=offset,
                               db_path=self.db_path)

    def get_user(self, user_id):
        self._authorize()
        return self._require_user(user_id)

    # ------------------------------------------------------ manage users
    def set_user_disabled(self, user_id, disabled, reason=None):
        """Block (or unblock) an account. Blocking ends its sessions."""
        self._authorize()
        user = self._require_user(user_id)
        if not isinstance(disabled, bool):
            raise AdminError("disabled must be True or False")
        if disabled and user_id == self.actor_id:
            raise AdminError("you cannot disable your own account")
        if reason is not None and (
                not isinstance(reason, str) or len(reason) > 200):
            raise AdminError("reason must be text of at most 200 characters")
        repo.set_account_disabled(user_id, disabled, reason, self.actor_id,
                                  db_path=self.db_path)
        ended = (self._sessions.end_all(user_id, ACCOUNT_CHANGED)
                 if disabled else 0)
        self._audit("disable_user" if disabled else "enable_user",
                    "user:%d:%s" % (user_id, user["username"]),
                    reason or ("sessions ended: %d" % ended))

    def reset_password(self, user_id, new_password):
        """Set a new password (min. length rules apply); ends sessions."""
        self._authorize()
        user = self._require_user(user_id)
        ok, message = validate_password(new_password)
        if not ok:
            raise AdminError(message)
        password_hash = bcrypt.hashpw(
            new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        repo.update_password_hash(user_id, password_hash,
                                  db_path=self.db_path)
        self._sessions.end_all(user_id, ACCOUNT_CHANGED)
        self._audit("reset_password",
                    "user:%d:%s" % (user_id, user["username"]))

    def delete_user(self, user_id):
        """Permanently delete an account with its scores and sessions."""
        self._authorize()
        user = self._require_user(user_id)
        if user_id == self.actor_id:
            raise AdminError("you cannot delete your own account")
        repo.delete_user(user_id, db_path=self.db_path)
        self._audit("delete_user",
                    "user:%d:%s" % (user_id, user["username"]),
                    "games deleted: %d" % user["games_played"])

    def grant_admin(self, user_id):
        self._authorize()
        user = self._require_user(user_id)
        if not repo.add_admin(user_id, granted_by=self.actor_id,
                              db_path=self.db_path):
            raise AdminError("%s is already an administrator"
                             % user["username"])
        self._audit("grant_admin",
                    "user:%d:%s" % (user_id, user["username"]))

    def revoke_admin(self, user_id):
        self._authorize()
        user = self._require_user(user_id)
        if not user["is_admin"]:
            raise AdminError("%s is not an administrator" % user["username"])
        if repo.count_admins(db_path=self.db_path) <= 1:
            raise AdminError("the last administrator cannot be removed")
        repo.remove_admin(user_id, db_path=self.db_path)
        self._audit("revoke_admin",
                    "user:%d:%s" % (user_id, user["username"]))

    # ------------------------------------------- manage leaderboard data
    def get_leaderboard(self, limit=50):
        self._authorize()
        _check_int(limit, "limit", 1)
        return get_leaderboard(limit=min(limit, MAX_PAGE),
                               db_path=self.db_path)

    def list_user_scores(self, user_id, limit=50):
        self._authorize()
        self._require_user(user_id)
        _check_int(limit, "limit", 1)
        return get_scores_for_user(user_id, limit=min(limit, MAX_PAGE),
                                   db_path=self.db_path)

    def delete_score(self, score_id):
        """Remove one suspicious score; the player's best is recomputed."""
        self._authorize()
        _check_int(score_id, "score_id", 1)
        owner = repo.delete_score(score_id, db_path=self.db_path)
        if owner is None:
            raise AdminError("unknown score: %d" % score_id)
        self._audit("delete_score", "score:%d" % score_id,
                    "owner user:%d" % owner)

    def reset_user_scores(self, user_id):
        """Wipe all of a player's scores and their leaderboard entry."""
        self._authorize()
        user = self._require_user(user_id)
        removed = repo.delete_user_scores(user_id, db_path=self.db_path)
        self._audit("reset_user_scores",
                    "user:%d:%s" % (user_id, user["username"]),
                    "scores deleted: %d" % removed)
        return removed

    def check_data_integrity(self):
        """Compare the leaderboard with the saved scores (SNAKE-SR-004).

        Returns ``scoring.integrity.IntegrityReport``; ``report.ok`` is True
        when nothing is wrong.
        """
        self._authorize()
        report = integrity.verify_integrity(db_path=self.db_path)
        self._audit("check_integrity", None,
                    "problems: %d" % len(report.problems))
        return report

    def rebuild_leaderboard(self):
        """Recompute every leaderboard row from the saved scores."""
        self._authorize()
        rows = integrity.rebuild_leaderboard(db_path=self.db_path)
        self._audit("rebuild_leaderboard", None, "rows: %d" % rows)
        return rows

    # ------------------------------------------------------- statistics
    def game_statistics(self):
        self._authorize()
        return stats.get_global_statistics(db_path=self.db_path)

    def player_statistics(self, user_id):
        self._authorize()
        self._require_user(user_id)
        return stats.get_player_statistics(user_id, db_path=self.db_path)

    # ---------------------------------------------------- configuration
    def get_config(self):
        self._authorize()
        return game_config.load_config(self.db_path)

    def set_config(self, key, value):
        self._authorize()
        try:
            clean = game_config.validate_value(key, value)
        except game_config.ConfigError as exc:
            raise AdminError(str(exc)) from exc
        repo.set_config_value(key, clean, self.actor_id,
                              db_path=self.db_path)
        self._audit("set_config", key, str(clean))

    def reset_config(self, key):
        """Go back to a parameter's default value."""
        self._authorize()
        if key not in game_config.PARAMETERS:
            raise AdminError("unknown parameter: %r" % (key,))
        repo.delete_config_value(key, db_path=self.db_path)
        self._audit("reset_config", key)

    # ------------------------------------------------------- audit log
    def audit_log(self, limit=100):
        self._authorize()
        _check_int(limit, "limit", 1)
        return repo.list_audit_entries(limit=min(limit, MAX_PAGE),
                                       db_path=self.db_path)
