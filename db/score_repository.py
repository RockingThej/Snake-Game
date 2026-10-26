"""Repository functions for completed game scores."""
from db.connection import get_connection


def save_score(user_id, score, mode, difficulty, db_path=None):
    """Persist a completed game and update that user's personal best.

    Score history and the leaderboard update are committed in one transaction.
    The leaderboard retains the first result when a later score ties the best.
    """
    if isinstance(score, bool) or not isinstance(score, int) or score < 0:
        raise ValueError("score must be a non-negative integer")
    if not isinstance(mode, str) or not mode.strip():
        raise ValueError("mode must not be empty")
    if not isinstance(difficulty, str) or not difficulty.strip():
        raise ValueError("difficulty must not be empty")

    connection = get_connection(db_path)
    try:
        with connection:
            cursor = connection.execute(
                "INSERT INTO scores (user_id, score, mode, difficulty) "
                "VALUES (?, ?, ?, ?)",
                (user_id, score, mode.strip(), difficulty.strip()),
            )
            score_id = cursor.lastrowid
            connection.execute(
                "INSERT INTO leaderboard "
                "(user_id, best_score, mode, difficulty, "
                "achieved_at, score_id) "
                "SELECT id, ?, ?, ?, "
                "(SELECT created_at FROM scores WHERE id = ?), ? "
                "FROM users WHERE id = ? "
                "ON CONFLICT(user_id) DO UPDATE SET "
                "best_score = excluded.best_score, mode = excluded.mode, "
                "difficulty = excluded.difficulty, "
                "achieved_at = excluded.achieved_at, "
                "score_id = excluded.score_id "
                "WHERE excluded.best_score > leaderboard.best_score",
                (score, mode.strip(), difficulty.strip(), score_id, score_id,
                 user_id),
            )
        return score_id
    finally:
        connection.close()


def get_scores_for_user(user_id, limit=100, db_path=None):
    """Return a user's most recent saved scores, newest first."""
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ValueError("limit must be a positive integer")

    connection = get_connection(db_path)
    try:
        rows = connection.execute(
            "SELECT id, user_id, score, mode, difficulty, created_at "
            "FROM scores "
            "WHERE user_id = ? ORDER BY created_at DESC, id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()
