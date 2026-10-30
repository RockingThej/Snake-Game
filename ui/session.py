"""Who is playing, and what happens to their result when a game ends.

No Pygame imports here, so it can be unit tested headless. The launcher
(main.py) attaches one Session to the ScreenManager as ``manager.session``.
"""
from db import get_leaderboard, get_user_by_username, save_score


class Session:
    def __init__(self, auth=None, db_path=None, on_game_over=None):
        if auth is None:
            from auth import DbAuth
            auth = DbAuth(db_path=db_path)
        self.auth = auth
        self.db_path = db_path
        self.on_game_over = on_game_over   # callback(state, saved: bool)
        self.user_id = None
        self.username = None

    @property
    def logged_in(self):
        return self.user_id is not None

    def login(self, username):
        """Remember an already-authenticated user. Return their id."""
        user = get_user_by_username(username.strip(), db_path=self.db_path)
        if user is None:
            raise ValueError("unknown user: %s" % username)
        self.user_id = user["id"]
        self.username = user["username"]
        return self.user_id

    def logout(self):
        self.user_id = None
        self.username = None

    def save_result(self, state):
        """Store a finished game for the logged-in user. Return the score id."""
        if not self.logged_in:
            return None
        return save_score(self.user_id, state.score, state.mode,
                          state.difficulty, db_path=self.db_path)

    def finish_game(self, state):
        """Called once by GameScreen when a game ends."""
        saved = self.save_result(state) is not None
        if self.on_game_over is not None:
            self.on_game_over(state, saved)
        return saved

    def leaderboard(self, limit=10):
        return get_leaderboard(limit=limit, db_path=self.db_path)
