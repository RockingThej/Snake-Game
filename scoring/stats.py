"""Statistics Module (S2-15): what players and administrators can look at.

Two read-only views, both returning plain dictionaries so any screen can
render them without knowing about the database:

``get_player_statistics(user_id)``  (SRS 7.1 "View Statistics")
    {
      "user_id", "username",
      "games_played", "best_score", "total_score", "average_score",
      "last_played",              # ISO timestamp or None
      "rank",                     # leaderboard position or None
      "by_mode":       [{"name", "games", "best", "average"}, ...],
      "by_difficulty": [{"name", "games", "best", "average"}, ...],
      "recent_scores": [{"score", "mode", "difficulty", "created_at"}, ...],
    }

``get_global_statistics()``  (SRS 7.2 "View Game Statistics", admin only)
    {
      "total_players", "total_games", "players_with_games",
      "average_score", "highest_score",   # None or {username, score, ...}
      "games_by_mode", "games_by_difficulty",
      "most_played_mode",                 # name or None
      "active_players_7d",
      "games_per_day",                    # 7 x {"date", "games"}, oldest first
    }

Averages are rounded to one decimal place. Dates are UTC.
"""
from datetime import date, datetime, timedelta, timezone

from db import stats_repository as repo

RECENT_SCORES = 10
TREND_DAYS = 7


def _round(value):
    return round(value, 1) if value is not None else 0.0


def _rounded_rows(rows):
    return [
        {"name": row["name"], "games": row["games"],
         "best": row["best"], "average": _round(row["average"])}
        for row in rows
    ]


def _check_user_id(user_id):
    if isinstance(user_id, bool) or not isinstance(user_id, int):
        raise ValueError("user_id must be an integer")


def get_player_statistics(user_id, *, db_path=None,
                          recent=RECENT_SCORES):
    """Return one player's statistics. Raise ValueError for unknown users."""
    _check_user_id(user_id)
    if isinstance(recent, bool) or not isinstance(recent, int) or recent < 0:
        raise ValueError("recent must be a non-negative integer")
    username = repo.player_exists(user_id, db_path=db_path)
    if username is None:
        raise ValueError("unknown user: %r" % (user_id,))

    totals = repo.get_player_totals(user_id, db_path=db_path)
    return {
        "user_id": user_id,
        "username": username,
        "games_played": totals["games"],
        "best_score": totals["best"],
        "total_score": totals["total"],
        "average_score": _round(totals["average"]),
        "last_played": totals["last_played"],
        "rank": repo.get_player_rank(user_id, db_path=db_path),
        "by_mode": _rounded_rows(
            repo.get_player_breakdown(user_id, "mode", db_path=db_path)),
        "by_difficulty": _rounded_rows(
            repo.get_player_breakdown(user_id, "difficulty",
                                      db_path=db_path)),
        "recent_scores": repo.get_recent_scores(
            user_id, recent, db_path=db_path) if recent else [],
    }


def _as_date(today):
    if today is None:
        return datetime.now(timezone.utc).date()
    if isinstance(today, datetime):
        return today.date()
    if isinstance(today, date):
        return today
    raise ValueError("today must be a date")


def get_global_statistics(*, db_path=None, today=None, days=TREND_DAYS):
    """Return statistics across all players (intended for administrators).

    ``today`` and ``days`` only exist so tests can pin the trend window.
    """
    if isinstance(days, bool) or not isinstance(days, int) or days < 1:
        raise ValueError("days must be a positive integer")
    last_day = _as_date(today)
    first_day = last_day - timedelta(days=days - 1)

    totals = repo.get_global_totals(db_path=db_path)
    by_mode = repo.get_games_grouped("mode", db_path=db_path)
    per_day = repo.get_games_per_day(
        first_day.isoformat(), last_day.isoformat(), db_path=db_path)

    return {
        "total_players": totals["total_players"],
        "total_games": totals["total_games"],
        "players_with_games": totals["players_with_games"],
        "average_score": _round(totals["average_score"]),
        "highest_score": repo.get_top_score(db_path=db_path),
        "games_by_mode": by_mode,
        "games_by_difficulty": repo.get_games_grouped(
            "difficulty", db_path=db_path),
        "most_played_mode": by_mode[0]["name"] if by_mode else None,
        "active_players_7d": repo.count_active_players(
            (last_day - timedelta(days=6)).isoformat(),
            last_day.isoformat(), db_path=db_path),
        "games_per_day": [
            {"date": day.isoformat(),
             "games": per_day.get(day.isoformat(), 0)}
            for day in (first_day + timedelta(days=offset)
                        for offset in range(days))
        ],
    }
