"""Application-level score rules and persistence for completed matches."""

from db.score_repository import save_scores
from db.user_repository import get_user_by_id


class ScoreManager:
    """Save one score for each authenticated participant in a battle."""

    def __init__(self, db_path=None):
        self.db_path = db_path

    def save_battle_result(self, game_state):
        """Persist per-player scores and return their score-row IDs.

        ``game_state.player_ids`` must map ``player1`` and ``player2`` to
        existing user IDs. Missing or invalid accounts are rejected before any
        score is written so a partially identified match is never recorded.
        """
        if getattr(game_state, "mode", None) != "two_player_battle":
            raise ValueError("game state must be a two-player battle")

        players = ("player1", "player2")
        player_ids = getattr(game_state, "player_ids", None) or {}
        scores = getattr(game_state, "scores", None) or {}
        users = {}
        for player in players:
            user_id = player_ids.get(player)
            score = scores.get(player)
            if (isinstance(user_id, bool) or not isinstance(user_id, int)
                    or user_id < 1):
                raise ValueError(f"{player} must be signed in to save results")
            if (isinstance(score, bool) or not isinstance(score, int)
                    or score < 0):
                raise ValueError(f"{player} score must be a non-negative integer")
            users[player] = get_user_by_id(user_id, db_path=self.db_path)
            if users[player] is None:
                raise ValueError(f"{player} account does not exist")

        saved_ids = save_scores(
            [(player_ids[player], scores[player]) for player in players],
            game_state.mode,
            game_state.difficulty,
            db_path=self.db_path,
        )
        return dict(zip(players, saved_ids))
