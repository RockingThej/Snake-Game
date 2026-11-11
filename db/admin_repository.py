"""Repository functions for the Administration module (S2-14).

All SQL for administrators, account status, game configuration and the
audit log lives here. Authorisation is NOT checked here: callers must go
through ``admin.AdminService``, which does.
"""
from contextlib import closing

from db.connection import get_connection


# ------------------------------------------------------------ administrators
def is_admin(user_id, db_path=None):
    with closing(get_connection(db_path)) as connection:
        return connection.execute(
            "SELECT 1 FROM admins WHERE user_id = ?", (user_id,)
        ).fetchone() is not None


def count_admins(db_path=None):
    with closing(get_connection(db_path)) as connection:
        return connection.execute(
            "SELECT COUNT(*) AS n FROM admins").fetchone()["n"]


def add_admin(user_id, granted_by=None, db_path=None):
    """Make a user an administrator. Return False if they already were."""
    with closing(get_connection(db_path)) as connection:
        with connection:
            cursor = connection.execute(
                "INSERT OR IGNORE INTO admins (user_id, granted_by) "
                "VALUES (?, ?)", (user_id, granted_by))
        return cursor.rowcount > 0


def remove_admin(user_id, db_path=None):
    with closing(get_connection(db_path)) as connection:
        with connection:
            cursor = connection.execute(
                "DELETE FROM admins WHERE user_id = ?", (user_id,))
        return cursor.rowcount > 0


# ----------------------------------------------------------- account status
def is_account_disabled(user_id, db_path=None):
    with closing(get_connection(db_path)) as connection:
        row = connection.execute(
            "SELECT disabled FROM account_status WHERE user_id = ?",
            (user_id,)).fetchone()
        return bool(row["disabled"]) if row is not None else False


def set_account_disabled(user_id, disabled, reason, changed_by,
                         db_path=None):
    with closing(get_connection(db_path)) as connection:
        with connection:
            connection.execute(
                "INSERT INTO account_status "
                "(user_id, disabled, reason, changed_by) "
                "VALUES (?, ?, ?, ?) "
                "ON CONFLICT(user_id) DO UPDATE SET "
                "disabled = excluded.disabled, reason = excluded.reason, "
                "changed_by = excluded.changed_by, "
                "changed_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')",
                (user_id, 1 if disabled else 0, reason, changed_by))


# -------------------------------------------------------------------- users
def _like_pattern(search):
    escaped = (search.replace("\\", "\\\\").replace("%", "\\%")
               .replace("_", "\\_"))
    return "%" + escaped + "%"


_USER_SELECT = (
    "SELECT u.id, u.username, u.created_at, "
    "(a.user_id IS NOT NULL) AS is_admin, "
    "COALESCE(s.disabled, 0) AS disabled, s.reason AS disabled_reason, "
    "(SELECT COUNT(*) FROM scores WHERE user_id = u.id) AS games_played, "
    "COALESCE((SELECT MAX(score) FROM scores WHERE user_id = u.id), 0) "
    "AS best_score "
    "FROM users u "
    "LEFT JOIN admins a ON a.user_id = u.id "
    "LEFT JOIN account_status s ON s.user_id = u.id "
)


def _user_row(row):
    data = dict(row)
    data["is_admin"] = bool(data["is_admin"])
    data["disabled"] = bool(data["disabled"])
    return data


def list_users(search=None, limit=50, offset=0, db_path=None):
    where, params = "", []
    if search:
        where = "WHERE u.username LIKE ? ESCAPE '\\' "
        params.append(_like_pattern(search))
    with closing(get_connection(db_path)) as connection:
        rows = connection.execute(
            _USER_SELECT + where +
            "ORDER BY u.username COLLATE NOCASE ASC LIMIT ? OFFSET ?",
            params + [limit, offset]).fetchall()
        return [_user_row(row) for row in rows]


def get_user(user_id, db_path=None):
    with closing(get_connection(db_path)) as connection:
        row = connection.execute(
            _USER_SELECT + "WHERE u.id = ?", (user_id,)).fetchone()
        return _user_row(row) if row is not None else None


def update_password_hash(user_id, password_hash, db_path=None):
    with closing(get_connection(db_path)) as connection:
        with connection:
            cursor = connection.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (password_hash, user_id))
        return cursor.rowcount > 0


def delete_user(user_id, db_path=None):
    """Delete an account. Scores, leaderboard row and sessions cascade."""
    with closing(get_connection(db_path)) as connection:
        with connection:
            cursor = connection.execute(
                "DELETE FROM users WHERE id = ?", (user_id,))
        return cursor.rowcount > 0


# ------------------------------------------------------- leaderboard data
_REFRESH_ENTRY = (
    "INSERT INTO leaderboard "
    "(user_id, best_score, mode, difficulty, achieved_at, score_id) "
    "SELECT user_id, score, mode, difficulty, created_at, id FROM scores "
    "WHERE user_id = ? ORDER BY score DESC, created_at ASC, id ASC LIMIT 1"
)


def refresh_leaderboard_entry(connection, user_id):
    """Recompute one player's leaderboard row from their saved scores.

    Must be called inside the caller's transaction.
    """
    connection.execute(
        "DELETE FROM leaderboard WHERE user_id = ?", (user_id,))
    connection.execute(_REFRESH_ENTRY, (user_id,))


def delete_score(score_id, db_path=None):
    """Delete one saved score and fix that player's leaderboard row.

    Return the owner's user id, or ``None`` if the score does not exist.
    """
    with closing(get_connection(db_path)) as connection:
        with connection:
            row = connection.execute(
                "SELECT user_id FROM scores WHERE id = ?",
                (score_id,)).fetchone()
            if row is None:
                return None
            connection.execute(
                "DELETE FROM scores WHERE id = ?", (score_id,))
            refresh_leaderboard_entry(connection, row["user_id"])
            return row["user_id"]


def delete_user_scores(user_id, db_path=None):
    """Delete every score of a player (and their leaderboard row)."""
    with closing(get_connection(db_path)) as connection:
        with connection:
            cursor = connection.execute(
                "DELETE FROM scores WHERE user_id = ?", (user_id,))
            refresh_leaderboard_entry(connection, user_id)
        return cursor.rowcount


# ---------------------------------------------------------------- config
def get_config_rows(db_path=None):
    with closing(get_connection(db_path)) as connection:
        rows = connection.execute(
            "SELECT key, value, updated_at FROM game_config ORDER BY key"
        ).fetchall()
        return [dict(row) for row in rows]


def set_config_value(key, value, updated_by, db_path=None):
    with closing(get_connection(db_path)) as connection:
        with connection:
            connection.execute(
                "INSERT INTO game_config (key, value, updated_by) "
                "VALUES (?, ?, ?) ON CONFLICT(key) DO UPDATE SET "
                "value = excluded.value, updated_by = excluded.updated_by, "
                "updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')",
                (key, str(value), updated_by))


def delete_config_value(key, db_path=None):
    with closing(get_connection(db_path)) as connection:
        with connection:
            cursor = connection.execute(
                "DELETE FROM game_config WHERE key = ?", (key,))
        return cursor.rowcount > 0


# ------------------------------------------------------------- audit log
def add_audit_entry(actor_id, actor_name, action, target=None, detail=None,
                    db_path=None):
    with closing(get_connection(db_path)) as connection:
        with connection:
            connection.execute(
                "INSERT INTO admin_audit_log "
                "(actor_id, actor_name, action, target, detail) "
                "VALUES (?, ?, ?, ?, ?)",
                (actor_id, actor_name, action, target, detail))


def list_audit_entries(limit=100, db_path=None):
    with closing(get_connection(db_path)) as connection:
        rows = connection.execute(
            "SELECT id, actor_name, action, target, detail, created_at "
            "FROM admin_audit_log ORDER BY id DESC LIMIT ?",
            (limit,)).fetchall()
        return [dict(row) for row in rows]
