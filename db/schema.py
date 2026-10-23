"""The complete SQLite schema, kept inside the database layer."""

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL COLLATE NOCASE UNIQUE
        CHECK (length(trim(username)) > 0),
    password_hash TEXT NOT NULL
        CHECK (length(trim(password_hash)) > 0),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    score INTEGER NOT NULL CHECK (score >= 0),
    mode TEXT NOT NULL CHECK (length(trim(mode)) > 0),
    difficulty TEXT NOT NULL CHECK (length(trim(difficulty)) > 0),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_scores_user_created
    ON scores(user_id, created_at DESC, id DESC);

CREATE TABLE IF NOT EXISTS leaderboard (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    best_score INTEGER NOT NULL CHECK (best_score >= 0),
    mode TEXT NOT NULL CHECK (length(trim(mode)) > 0),
    difficulty TEXT NOT NULL CHECK (length(trim(difficulty)) > 0),
    achieved_at TEXT NOT NULL,
    score_id INTEGER NOT NULL UNIQUE REFERENCES scores(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_leaderboard_score
    ON leaderboard(best_score DESC, achieved_at ASC, user_id ASC);
"""

TABLE_NAMES = ("users", "scores", "leaderboard")
