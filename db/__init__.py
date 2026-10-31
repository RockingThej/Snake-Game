"""SQLite persistence layer for accounts, scores, and leaderboard data."""

from db.connection import DEFAULT_DB_PATH, get_table_names, initialize_database
from db.leaderboard_repository import get_leaderboard
from db.score_repository import get_scores_for_user, save_score, save_scores
from db.user_repository import (
    UserAlreadyExistsError,
    create_user,
    get_user_by_id,
    get_user_by_username,
)

__all__ = [
    "DEFAULT_DB_PATH",
    "UserAlreadyExistsError",
    "create_user",
    "get_leaderboard",
    "get_scores_for_user",
    "get_table_names",
    "get_user_by_id",
    "get_user_by_username",
    "initialize_database",
    "save_score",
    "save_scores",
]
