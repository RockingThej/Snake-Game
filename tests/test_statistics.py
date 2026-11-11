"""S2-15: Statistics module (player and global statistics)."""
import sqlite3
from datetime import date

import pytest

from db import create_user, initialize_database, save_score
from scoring.stats import get_global_statistics, get_player_statistics

TODAY = date(2026, 11, 10)


@pytest.fixture()
def db_path(tmp_path):
    path = str(tmp_path / "stats.sqlite3")
    initialize_database(path)
    return path


@pytest.fixture()
def alice(db_path):
    return create_user("Alice", "hash-a", db_path)


@pytest.fixture()
def bob(db_path):
    return create_user("Bob", "hash-b", db_path)


def add_score_on(db_path, user_id, score, mode, difficulty, day):
    """Insert a score with a chosen date (save_score always uses 'now')."""
    connection = sqlite3.connect(db_path)
    try:
        with connection:
            connection.execute(
                "INSERT INTO scores (user_id, score, mode, difficulty, "
                "created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, score, mode, difficulty, day + "T12:00:00.000Z"),
            )
    finally:
        connection.close()


# ----------------------------------------------------------- per player
def test_player_with_no_games(db_path, alice):
    stats = get_player_statistics(alice, db_path=db_path)
    assert stats["username"] == "Alice"
    assert stats["games_played"] == 0
    assert stats["best_score"] == 0
    assert stats["average_score"] == 0.0
    assert stats["total_score"] == 0
    assert stats["last_played"] is None
    assert stats["rank"] is None
    assert stats["by_mode"] == [] and stats["by_difficulty"] == []
    assert stats["recent_scores"] == []


def test_player_totals_and_average(db_path, alice):
    for score in (10, 20, 45):
        save_score(alice, score, "classic", "easy", db_path)
    stats = get_player_statistics(alice, db_path=db_path)
    assert stats["games_played"] == 3
    assert stats["best_score"] == 45
    assert stats["total_score"] == 75
    assert stats["average_score"] == 25.0
    assert stats["last_played"] is not None


def test_average_is_rounded_to_one_decimal(db_path, alice):
    for score in (10, 10, 11):
        save_score(alice, score, "classic", "easy", db_path)
    assert get_player_statistics(
        alice, db_path=db_path)["average_score"] == 10.3


def test_breakdown_by_mode_and_difficulty(db_path, alice):
    save_score(alice, 30, "classic", "easy", db_path)
    save_score(alice, 50, "classic", "hard", db_path)
    save_score(alice, 80, "survival", "hard", db_path)
    stats = get_player_statistics(alice, db_path=db_path)
    assert stats["by_mode"] == [
        {"name": "classic", "games": 2, "best": 50, "average": 40.0},
        {"name": "survival", "games": 1, "best": 80, "average": 80.0},
    ]
    assert [row["name"] for row in stats["by_difficulty"]] == ["hard",
                                                               "easy"]
    assert stats["by_difficulty"][0]["average"] == 65.0


def test_recent_scores_are_newest_first_and_limited(db_path, alice):
    for score in range(1, 15):
        save_score(alice, score, "classic", "easy", db_path)
    stats = get_player_statistics(alice, db_path=db_path)
    assert [row["score"] for row in stats["recent_scores"]] == list(
        range(14, 4, -1))
    short = get_player_statistics(alice, db_path=db_path, recent=3)
    assert len(short["recent_scores"]) == 3
    none = get_player_statistics(alice, db_path=db_path, recent=0)
    assert none["recent_scores"] == []


def test_rank_matches_the_leaderboard(db_path, alice, bob):
    carol = create_user("Carol", "hash-c", db_path)
    save_score(alice, 40, "classic", "easy", db_path)
    save_score(bob, 90, "classic", "easy", db_path)
    save_score(carol, 65, "classic", "easy", db_path)
    ranks = {name: get_player_statistics(uid, db_path=db_path)["rank"]
             for name, uid in (("alice", alice), ("bob", bob),
                               ("carol", carol))}
    assert ranks == {"bob": 1, "carol": 2, "alice": 3}


def test_players_are_counted_separately(db_path, alice, bob):
    save_score(alice, 10, "classic", "easy", db_path)
    save_score(bob, 99, "survival", "hard", db_path)
    stats = get_player_statistics(alice, db_path=db_path)
    assert stats["games_played"] == 1 and stats["best_score"] == 10


@pytest.mark.parametrize("bad", [None, "1", 1.5, True])
def test_player_stats_reject_bad_user_ids(db_path, bad):
    with pytest.raises(ValueError):
        get_player_statistics(bad, db_path=db_path)


def test_player_stats_reject_unknown_user(db_path):
    with pytest.raises(ValueError):
        get_player_statistics(424242, db_path=db_path)


def test_player_stats_reject_bad_recent(db_path, alice):
    for bad in (-1, True, "3"):
        with pytest.raises(ValueError):
            get_player_statistics(alice, db_path=db_path, recent=bad)


# ------------------------------------------------------------- global
def test_global_statistics_on_an_empty_database(db_path):
    stats = get_global_statistics(db_path=db_path, today=TODAY)
    assert stats["total_players"] == 0
    assert stats["total_games"] == 0
    assert stats["average_score"] == 0.0
    assert stats["highest_score"] is None
    assert stats["most_played_mode"] is None
    assert stats["games_by_mode"] == []
    assert len(stats["games_per_day"]) == 7
    assert all(day["games"] == 0 for day in stats["games_per_day"])


def test_global_totals(db_path, alice, bob):
    create_user("Idle", "hash-i", db_path)       # never plays
    save_score(alice, 20, "classic", "easy", db_path)
    save_score(alice, 60, "classic", "hard", db_path)
    save_score(bob, 100, "survival", "hard", db_path)
    stats = get_global_statistics(db_path=db_path, today=TODAY)
    assert stats["total_players"] == 3
    assert stats["players_with_games"] == 2
    assert stats["total_games"] == 3
    assert stats["average_score"] == 60.0
    assert stats["highest_score"]["username"] == "Bob"
    assert stats["highest_score"]["score"] == 100
    assert stats["most_played_mode"] == "classic"
    assert stats["games_by_mode"] == [
        {"name": "classic", "games": 2}, {"name": "survival", "games": 1}]
    assert stats["games_by_difficulty"] == [
        {"name": "hard", "games": 2}, {"name": "easy", "games": 1}]


def test_games_per_day_is_zero_filled_and_ordered(db_path, alice, bob):
    add_score_on(db_path, alice, 10, "classic", "easy", "2026-11-10")
    add_score_on(db_path, alice, 20, "classic", "easy", "2026-11-10")
    add_score_on(db_path, bob, 30, "classic", "easy", "2026-11-08")
    add_score_on(db_path, bob, 40, "classic", "easy", "2026-10-01")  # old
    stats = get_global_statistics(db_path=db_path, today=TODAY)
    days = {row["date"]: row["games"] for row in stats["games_per_day"]}
    assert list(days) == sorted(days)
    assert list(days)[0] == "2026-11-04" and list(days)[-1] == "2026-11-10"
    assert days["2026-11-10"] == 2
    assert days["2026-11-08"] == 1
    assert days["2026-11-05"] == 0
    assert "2026-10-01" not in days
    assert stats["active_players_7d"] == 2


def test_active_players_ignores_old_games(db_path, alice, bob):
    add_score_on(db_path, alice, 10, "classic", "easy", "2026-11-09")
    add_score_on(db_path, bob, 10, "classic", "easy", "2026-09-01")
    stats = get_global_statistics(db_path=db_path, today=TODAY)
    assert stats["active_players_7d"] == 1


def test_global_stats_reject_bad_arguments(db_path):
    with pytest.raises(ValueError):
        get_global_statistics(db_path=db_path, days=0)
    with pytest.raises(ValueError):
        get_global_statistics(db_path=db_path, today="2026-11-10")


def test_statistics_never_change_the_data(db_path, alice):
    save_score(alice, 10, "classic", "easy", db_path)
    connection = sqlite3.connect(db_path)
    try:
        before = connection.execute(
            "SELECT * FROM scores ORDER BY id").fetchall()
    finally:
        connection.close()
    get_player_statistics(alice, db_path=db_path)
    get_global_statistics(db_path=db_path, today=TODAY)
    connection = sqlite3.connect(db_path)
    try:
        after = connection.execute(
            "SELECT * FROM scores ORDER BY id").fetchall()
    finally:
        connection.close()
    assert before == after


def test_cannot_group_by_arbitrary_column(db_path):
    from db import stats_repository
    with pytest.raises(ValueError):
        stats_repository.get_games_grouped("password_hash; DROP TABLE x",
                                           db_path=db_path)
