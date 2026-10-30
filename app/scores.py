"""S1-17: Score Manager - calculation and save."""
from flask import Blueprint, g, jsonify, request

from .auth import login_required
from .db import get_db
from .validators import (MAX_DURATION_SECONDS, MAX_FOOD_EATEN, MAX_SCORE,
                         ValidationError, validate_difficulty, validate_int)

bp = Blueprint("scores", __name__, url_prefix="/api/scores")

POINTS_PER_FOOD = 10
DIFFICULTY_MULTIPLIER = {"easy": 1.0, "normal": 1.5, "hard": 2.0}
# Small bonus for surviving: 1 point per 10 seconds, only if you ate something.
SECONDS_PER_BONUS_POINT = 10


class ScoreManager:
    """Calculates and stores scores. The server computes the score so that
    clients can't just submit any number they like."""

    @staticmethod
    def calculate_score(food_eaten, duration_seconds, difficulty="normal"):
        food_eaten = validate_int(food_eaten, "food_eaten", 0, MAX_FOOD_EATEN)
        duration_seconds = validate_int(
            duration_seconds, "duration_seconds", 0, MAX_DURATION_SECONDS
        )
        difficulty = validate_difficulty(difficulty)

        base = food_eaten * POINTS_PER_FOOD
        bonus = (duration_seconds //
                 SECONDS_PER_BONUS_POINT) if food_eaten > 0 else 0
        score = int((base + bonus) * DIFFICULTY_MULTIPLIER[difficulty])
        return min(score, MAX_SCORE)

    @staticmethod
    def save_score(user_id, food_eaten, duration_seconds, difficulty="normal"):
        score = ScoreManager.calculate_score(
            food_eaten, duration_seconds, difficulty)
        difficulty = validate_difficulty(difficulty)
        db = get_db()
        cur = db.execute(
            "INSERT INTO scores (user_id, score, food_eaten, duration_seconds, difficulty) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, score, food_eaten, duration_seconds, difficulty),
        )
        db.commit()
        return {"id": cur.lastrowid, "score": score}

    @staticmethod
    def get_user_scores(user_id, limit=20):
        rows = get_db().execute(
            "SELECT id, score, food_eaten, duration_seconds, difficulty, created_at "
            "FROM scores WHERE user_id = ? ORDER BY created_at DESC, id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_best_score(user_id):
        row = get_db().execute(
            "SELECT MAX(score) AS best FROM scores WHERE user_id = ?", (user_id,)
        ).fetchone()
        return row["best"] or 0


@bp.errorhandler(ValidationError)
def handle_validation_error(err):
    return jsonify(error=err.message, field=err.field), 400


@bp.post("")
@login_required
def submit_score():
    data = request.get_json(silent=True) or {}
    result = ScoreManager.save_score(
        g.user["id"],
        data.get("food_eaten"),
        data.get("duration_seconds"),
        data.get("difficulty", "normal"),
    )
    return jsonify(result), 201


@bp.get("/me")
@login_required
def my_scores():
    return jsonify(
        best=ScoreManager.get_best_score(g.user["id"]),
        scores=ScoreManager.get_user_scores(g.user["id"]),
    )
