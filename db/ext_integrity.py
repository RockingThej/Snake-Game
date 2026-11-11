"""S2-16: database-level guards for scores and the leaderboard (SNAKE-SR-004).

* A saved score can never be edited, only deleted (by an administrator).
* A leaderboard row must always describe a real saved score exactly, so
  nobody can write "999999" into the leaderboard without playing for it.

The existing ``save_score`` already satisfies both rules, so it keeps
working unchanged. The guards are (re)installed every time the database is
opened, so dropping them has no lasting effect.
"""

_MATCHES_A_SAVED_SCORE = """
WHEN NOT EXISTS (
    SELECT 1 FROM scores AS s
    WHERE s.id = NEW.score_id
      AND s.user_id = NEW.user_id
      AND s.score = NEW.best_score
      AND s.mode = NEW.mode
      AND s.difficulty = NEW.difficulty
      AND s.created_at = NEW.achieved_at
)
BEGIN
    SELECT RAISE(ABORT, 'leaderboard entry must match a saved score');
END;
"""

SQL = """
CREATE TRIGGER IF NOT EXISTS scores_are_immutable
BEFORE UPDATE ON scores
BEGIN
    SELECT RAISE(ABORT, 'saved scores cannot be modified');
END;

CREATE TRIGGER IF NOT EXISTS leaderboard_matches_score_on_insert
BEFORE INSERT ON leaderboard
""" + _MATCHES_A_SAVED_SCORE + """

CREATE TRIGGER IF NOT EXISTS leaderboard_matches_score_on_update
BEFORE UPDATE ON leaderboard
""" + _MATCHES_A_SAVED_SCORE
