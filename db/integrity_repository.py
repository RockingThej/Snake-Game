"""Consistency checks and repair for scores and the leaderboard (S2-16)."""
from contextlib import closing

from db.connection import get_connection


def find_leaderboard_problems(db_path=None):
    """Return a list of ``{"kind", "user_id", "score_id", "detail"}`` rows
    describing leaderboard rows that disagree with the saved scores."""
    problems = []
    with closing(get_connection(db_path)) as connection:
        # 1. A leaderboard row that does not match the score it points to.
        rows = connection.execute(
            "SELECT l.user_id, l.score_id, l.best_score, s.score AS real "
            "FROM leaderboard l LEFT JOIN scores s ON s.id = l.score_id "
            "WHERE s.id IS NULL OR s.user_id != l.user_id "
            "OR s.score != l.best_score OR s.mode != l.mode "
            "OR s.difficulty != l.difficulty "
            "OR s.created_at != l.achieved_at").fetchall()
        for row in rows:
            problems.append({
                "kind": "leaderboard_mismatch", "user_id": row["user_id"],
                "score_id": row["score_id"],
                "detail": "leaderboard says %s, saved score is %s" % (
                    row["best_score"], row["real"])})

        # 2. A leaderboard row that is not the player's best score.
        rows = connection.execute(
            "SELECT l.user_id, l.score_id, l.best_score, "
            "(SELECT MAX(score) FROM scores WHERE user_id = l.user_id) "
            "AS best FROM leaderboard l "
            "WHERE l.best_score != "
            "(SELECT MAX(score) FROM scores WHERE user_id = l.user_id)"
        ).fetchall()
        for row in rows:
            problems.append({
                "kind": "leaderboard_not_best", "user_id": row["user_id"],
                "score_id": row["score_id"],
                "detail": "leaderboard says %s, player's best is %s" % (
                    row["best_score"], row["best"])})

        # 3. A player with saved scores but no leaderboard row.
        rows = connection.execute(
            "SELECT DISTINCT user_id FROM scores WHERE user_id NOT IN "
            "(SELECT user_id FROM leaderboard)").fetchall()
        for row in rows:
            problems.append({
                "kind": "missing_leaderboard_entry",
                "user_id": row["user_id"], "score_id": None,
                "detail": "player has scores but no leaderboard entry"})
    return problems


def list_saved_scores(db_path=None):
    """Every saved score as ``(id, user_id, score, mode, difficulty)``."""
    with closing(get_connection(db_path)) as connection:
        return [tuple(row) for row in connection.execute(
            "SELECT id, user_id, score, mode, difficulty FROM scores "
            "ORDER BY id").fetchall()]


def count_leaderboard_rows(db_path=None):
    with closing(get_connection(db_path)) as connection:
        return connection.execute(
            "SELECT COUNT(*) AS n FROM leaderboard").fetchone()["n"]


def rebuild_leaderboard(db_path=None):
    """Recompute every player's leaderboard row from the saved scores.

    Ties keep the earliest result, like ``save_score``. Return the number
    of rows written.
    """
    with closing(get_connection(db_path)) as connection:
        with connection:
            connection.execute("DELETE FROM leaderboard")
            cursor = connection.execute(
                "INSERT INTO leaderboard (user_id, best_score, mode, "
                "difficulty, achieved_at, score_id) "
                "SELECT user_id, score, mode, difficulty, created_at, id "
                "FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY user_id "
                "ORDER BY score DESC, created_at ASC, id ASC) AS rn "
                "FROM scores) WHERE rn = 1")
        return cursor.rowcount
