"""Read-only aggregate queries for the Statistics module (S2-15).

Nothing here changes data. ``scoring/stats.py`` turns these rows into the
dictionaries the UI and the administration module use.
"""
from contextlib import closing

from db.connection import get_connection

# Column names cannot be bound as SQL parameters, so only these are allowed.
_GROUPABLE = ("mode", "difficulty")


def _group_column(column):
    if column not in _GROUPABLE:
        raise ValueError("cannot group scores by %r" % (column,))
    return column


def player_exists(user_id, db_path=None):
    with closing(get_connection(db_path)) as connection:
        row = connection.execute(
            "SELECT username FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return row["username"] if row is not None else None


def get_player_totals(user_id, db_path=None):
    """Games played, best, total and average score, and last played time."""
    with closing(get_connection(db_path)) as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS games, COALESCE(MAX(score), 0) AS best, "
            "COALESCE(SUM(score), 0) AS total, AVG(score) AS average, "
            "MAX(created_at) AS last_played "
            "FROM scores WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        return dict(row)


def get_player_breakdown(user_id, column, db_path=None):
    """Per-mode or per-difficulty games, best and average for one player."""
    column = _group_column(column)
    with closing(get_connection(db_path)) as connection:
        rows = connection.execute(
            "SELECT %s AS name, COUNT(*) AS games, MAX(score) AS best, "
            "AVG(score) AS average FROM scores WHERE user_id = ? "
            "GROUP BY %s ORDER BY games DESC, name ASC" % (column, column),
            (user_id,),
        ).fetchall()
        return [dict(row) for row in rows]


def get_recent_scores(user_id, limit, db_path=None):
    with closing(get_connection(db_path)) as connection:
        rows = connection.execute(
            "SELECT score, mode, difficulty, created_at FROM scores "
            "WHERE user_id = ? ORDER BY created_at DESC, id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return [dict(row) for row in rows]


def get_player_rank(user_id, db_path=None):
    """Leaderboard position (1 = best), or ``None`` if not on the board.

    Uses the same ordering as ``db.get_leaderboard``.
    """
    with closing(get_connection(db_path)) as connection:
        row = connection.execute(
            "SELECT position FROM ("
            "  SELECT leaderboard.user_id AS user_id, "
            "         ROW_NUMBER() OVER (ORDER BY leaderboard.best_score "
            "         DESC, leaderboard.achieved_at ASC, "
            "         users.username COLLATE NOCASE ASC) AS position "
            "  FROM leaderboard JOIN users "
            "    ON users.id = leaderboard.user_id"
            ") WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        return row["position"] if row is not None else None


def get_global_totals(db_path=None):
    with closing(get_connection(db_path)) as connection:
        players = connection.execute(
            "SELECT COUNT(*) AS n FROM users"
        ).fetchone()["n"]
        games = connection.execute(
            "SELECT COUNT(*) AS games, AVG(score) AS average, "
            "COUNT(DISTINCT user_id) AS players_with_games FROM scores"
        ).fetchone()
        return {
            "total_players": players,
            "total_games": games["games"],
            "average_score": games["average"],
            "players_with_games": games["players_with_games"],
        }


def get_games_grouped(column, db_path=None):
    """Games played across all players, grouped by mode or difficulty."""
    column = _group_column(column)
    with closing(get_connection(db_path)) as connection:
        rows = connection.execute(
            "SELECT %s AS name, COUNT(*) AS games FROM scores "
            "GROUP BY %s ORDER BY games DESC, name ASC" % (column, column)
        ).fetchall()
        return [dict(row) for row in rows]


def get_top_score(db_path=None):
    with closing(get_connection(db_path)) as connection:
        row = connection.execute(
            "SELECT users.username, scores.score, scores.mode, "
            "scores.difficulty, scores.created_at "
            "FROM scores JOIN users ON users.id = scores.user_id "
            "ORDER BY scores.score DESC, scores.created_at ASC, "
            "scores.id ASC LIMIT 1"
        ).fetchone()
        return dict(row) if row is not None else None


def get_games_per_day(first_day, last_day, db_path=None):
    """Games per UTC day between two ISO dates (inclusive); missing days
    are not returned."""
    with closing(get_connection(db_path)) as connection:
        rows = connection.execute(
            "SELECT date(created_at) AS day, COUNT(*) AS games "
            "FROM scores WHERE date(created_at) BETWEEN ? AND ? "
            "GROUP BY day ORDER BY day",
            (first_day, last_day),
        ).fetchall()
        return {row["day"]: row["games"] for row in rows}


def count_active_players(first_day, last_day, db_path=None):
    with closing(get_connection(db_path)) as connection:
        return connection.execute(
            "SELECT COUNT(DISTINCT user_id) AS n FROM scores "
            "WHERE date(created_at) BETWEEN ? AND ?",
            (first_day, last_day),
        ).fetchone()["n"]
