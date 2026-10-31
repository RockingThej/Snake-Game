"""Repository functions for completed game scores."""
from db.connection import get_connection


def _validate_score(score, mode, difficulty):
    if isinstance(score, bool) or not isinstance(score, int) or score < 0:
        raise ValueError("score must be a non-negative integer")
    if not isinstance(mode, str) or not mode.strip():
        raise ValueError("mode must not be empty")
    if not isinstance(difficulty, str) or not difficulty.strip():
        raise ValueError("difficulty must not be empty")


def _record_score(connection, user_id, score, mode, difficulty):
    cursor = connection.execute(
        "INSERT INTO scores (user_id, score, mode, difficulty) "
        "VALUES (?, ?, ?, ?)",
        (user_id, score, mode.strip(), difficulty.strip()),
    )
    score_id = cursor.lastrowid
    connection.execute(
        "INSERT INTO leaderboard "
        "(user_id, best_score, mode, difficulty, achieved_at, score_id) "
        "SELECT id, ?, ?, ?, "
        "(SELECT created_at FROM scores WHERE id = ?), ? "
        "FROM users WHERE id = ? "
        "ON CONFLICT(user_id) DO UPDATE SET "
        "best_score = excluded.best_score, mode = excluded.mode, "
        "difficulty = excluded.difficulty, "
        "achieved_at = excluded.achieved_at, score_id = excluded.score_id "
        "WHERE excluded.best_score > leaderboard.best_score",
        (score, mode.strip(), difficulty.strip(), score_id, score_id, user_id),
    )
    return score_id


def save_score(user_id, score, mode, difficulty, db_path=None):
    """Persist a completed game and update that user's personal best."""
    return save_scores([(user_id, score)], mode, difficulty, db_path)[0]


def save_scores(user_scores, mode, difficulty, db_path=None):
    """Persist multiple completed-game scores in one transaction.

    ``user_scores`` is a sequence of ``(user_id, score)`` pairs. The
    leaderboard retains the first result when a later score ties the best.
    """
    if not isinstance(user_scores, (list, tuple)) or not user_scores:
        raise ValueError("at least one user score is required")
    for user_id, score in user_scores:
        if isinstance(user_id, bool) or not isinstance(user_id, int):
            raise ValueError("user_id must be an integer")
        _validate_score(score, mode, difficulty)

    connection = get_connection(db_path)
    try:
        with connection:
            score_ids = [
                _record_score(connection, user_id, score, mode, difficulty)
                for user_id, score in user_scores
            ]
        return score_ids
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
