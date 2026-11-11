"""Score and leaderboard integrity (S2-16, SNAKE-SR-004, SNAKE-SO-002).

Four layers, from the player's side inwards:

1. ``validate_result``  rejects impossible results (unknown mode or
   difficulty, negative or absurdly large scores) before they are stored.
2. ``submit_score``     is the one write path for players: it only accepts a
   result for the logged-in player themselves.
3. Database triggers (``db/ext_integrity.py``) refuse edits to saved scores
   and leaderboard rows that do not match a real score.
4. ``verify_integrity`` / ``rebuild_leaderboard`` let an administrator detect
   and repair damage (for example after someone edited the database file).

Limit: a desktop game cannot stop a person who edits the SQLite file with
their own tools; layers 3 and 4 make that visible and repairable, and layers
1 and 2 stop every route that goes through the game itself.
"""
from dataclasses import dataclass, field

from db import integrity_repository as repo
from db import save_score
from modes.difficulty import DifficultyManager
from modes.manager import GameModeManager

DEFAULT_MAX_SCORE = 1_000_000


class ScoreIntegrityError(ValueError):
    """Base class for rejected score data."""


class InvalidScoreError(ScoreIntegrityError):
    """The mode, difficulty or score value is not acceptable."""


class ScoreAccessError(PermissionError):
    """A player tried to save a score for someone else."""


def valid_modes():
    return tuple(mode.id for mode in GameModeManager.DEFAULT_MODES)


def valid_difficulties():
    return tuple(DifficultyManager.DEFAULT_SPEEDS_MS)


def validate_result(score, mode, difficulty, max_score=DEFAULT_MAX_SCORE):
    """Return ``(score, mode, difficulty)`` normalised, or raise
    ``InvalidScoreError``."""
    if isinstance(score, bool) or not isinstance(score, int):
        raise InvalidScoreError("score must be a whole number")
    if score < 0:
        raise InvalidScoreError("score cannot be negative")
    if score > max_score:
        raise InvalidScoreError("score is above the allowed maximum")
    if not isinstance(mode, str) or mode.strip().lower() not in valid_modes():
        raise InvalidScoreError("unknown game mode")
    if (not isinstance(difficulty, str)
            or difficulty.strip().lower() not in valid_difficulties()):
        raise InvalidScoreError("unknown difficulty")
    return score, mode.strip().lower(), difficulty.strip().lower()


def configured_max_score(db_path=None):
    """The administrator-configured maximum (see ``admin.config``)."""
    from admin import config      # imported here: admin uses this module
    return config.load_config(db_path)["score.max_per_game"]


def submit_score(user_id, score, mode, difficulty, *, actor_id=None,
                 max_score=None, db_path=None):
    """Validate and store a finished game. Return the new score id.

    ``actor_id`` is the logged-in player making the request; when given it
    must equal ``user_id``. Raise ``ScoreAccessError`` or
    ``InvalidScoreError`` instead of storing anything suspicious.
    """
    if actor_id is not None and actor_id != user_id:
        raise ScoreAccessError("players can only save their own scores")
    if max_score is None:
        max_score = configured_max_score(db_path)
    score, mode, difficulty = validate_result(score, mode, difficulty,
                                              max_score)
    return save_score(user_id, score, mode, difficulty, db_path=db_path)


@dataclass
class IntegrityReport:
    scores_checked: int = 0
    leaderboard_rows: int = 0
    problems: list = field(default_factory=list)

    @property
    def ok(self):
        return not self.problems


def verify_integrity(db_path=None, max_score=None):
    """Check saved scores and the leaderboard for inconsistencies."""
    if max_score is None:
        max_score = configured_max_score(db_path)
    report = IntegrityReport()
    scores = repo.list_saved_scores(db_path=db_path)
    report.scores_checked = len(scores)
    report.leaderboard_rows = repo.count_leaderboard_rows(db_path=db_path)

    for score_id, user_id, score, mode, difficulty in scores:
        try:
            validate_result(score, mode, difficulty, max_score)
        except InvalidScoreError as exc:
            report.problems.append({
                "kind": "invalid_score", "user_id": user_id,
                "score_id": score_id, "detail": str(exc)})
    report.problems.extend(repo.find_leaderboard_problems(db_path=db_path))
    return report


def rebuild_leaderboard(db_path=None):
    """Recompute the leaderboard from the saved scores (administrators)."""
    return repo.rebuild_leaderboard(db_path=db_path)
