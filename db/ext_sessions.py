"""S2-13: server-side login sessions (SNAKE-SR-005).

Only a SHA-256 hash of the session token is stored, never the token itself,
so a leaked database cannot be used to impersonate a logged-in player.
Times are epoch seconds so the session policy can be tested with a fake clock.
"""

SQL = """
CREATE TABLE IF NOT EXISTS auth_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_hash TEXT NOT NULL UNIQUE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at REAL NOT NULL,
    last_seen_at REAL NOT NULL,
    expires_at REAL NOT NULL,
    ended_at REAL,
    end_reason TEXT
);

CREATE INDEX IF NOT EXISTS idx_auth_sessions_user
    ON auth_sessions(user_id, ended_at);
"""
