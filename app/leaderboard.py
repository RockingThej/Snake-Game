"""S1-18: Basic Leaderboard - top players by best score."""
from flask import Blueprint, jsonify, request

from .db import get_db
from .validators import ValidationError, validate_limit

bp = Blueprint("leaderboard", __name__, url_prefix="/api/leaderboard")


def get_top_players(limit=10):
    rows = get_db().execute(
        """
        SELECT u.username,
               MAX(s.score) AS best_score,
               COUNT(s.id)  AS games_played
        FROM scores s
        JOIN users u ON u.id = s.user_id
        GROUP BY u.id
        ORDER BY best_score DESC, MIN(s.created_at) ASC, u.username ASC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [
        {"rank": i, "username": r["username"],
         "best_score": r["best_score"], "games_played": r["games_played"]}
        for i, r in enumerate(rows, start=1)
    ]


@bp.get("")
def leaderboard():
    try:
        limit = validate_limit(request.args.get("limit"))
    except ValidationError as err:
        return jsonify(error=err.message, field=err.field), 400
    return jsonify(leaderboard=get_top_players(limit))
