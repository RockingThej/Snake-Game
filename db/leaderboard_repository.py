"""Repository functions for ranked personal-best scores."""
from db.connection import get_connection


def get_leaderboard(limit=10, db_path=None):
    """Return personal bests ordered by score, then earliest achievement."""
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ValueError("limit must be a positive integer")

    connection = get_connection(db_path)
    try:
        rows = connection.execute(
            "SELECT users.id AS user_id, users.username, "
            "leaderboard.best_score "
            "AS score, leaderboard.mode, leaderboard.difficulty, "
            "leaderboard.achieved_at "
            "FROM leaderboard JOIN users ON users.id = leaderboard.user_id "
            "ORDER BY leaderboard.best_score DESC, "
            "leaderboard.achieved_at ASC, users.username COLLATE NOCASE ASC "
            "LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()
