"""S2-16: score and leaderboard integrity (SNAKE-SR-004, TC-SEC-004)."""
import sqlite3

import pytest

from admin import AdminService, PermissionDeniedError
from auth.guarded_session import GuardedSession
from db import (
    create_user,
    get_leaderboard,
    get_scores_for_user,
    initialize_database,
    save_score,
)
from db import admin_repository as admin_repo
from engine.game_state import GameState
from scoring import integrity
from scoring.integrity import (
    InvalidScoreError,
    ScoreAccessError,
    submit_score,
    validate_result,
    verify_integrity,
)


@pytest.fixture()
def db_path(tmp_path):
    path = str(tmp_path / "integrity.sqlite3")
    initialize_database(path)
    return path


@pytest.fixture()
def alice(db_path):
    return create_user("alice", "hash-a", db_path)


@pytest.fixture()
def bob(db_path):
    return create_user("bob", "hash-b", db_path)


def raw(db_path):
    """A plain connection that bypasses the game's own code."""
    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


# ------------------------------------------------------------ validation
def test_validate_result_normalises_valid_input():
    assert validate_result(50, " Classic ", "EASY") == (50, "classic", "easy")
    assert validate_result(0, "power_up", "hard") == (0, "power_up", "hard")


def test_every_registered_mode_and_difficulty_is_accepted():
    for mode in integrity.valid_modes():
        for difficulty in integrity.valid_difficulties():
            validate_result(1, mode, difficulty)
    assert set(integrity.valid_modes()) == {
        "classic", "obstacle", "power_up", "two_player_battle", "survival"}


@pytest.mark.parametrize("score", [-1, 1.5, True, "50", None, 10**9])
def test_invalid_scores_are_rejected(score):
    with pytest.raises(InvalidScoreError):
        validate_result(score, "classic", "easy")


@pytest.mark.parametrize("mode", ["", "cheat", None, 3, "classic'; --"])
def test_invalid_modes_are_rejected(mode):
    with pytest.raises(InvalidScoreError):
        validate_result(10, mode, "easy")


@pytest.mark.parametrize("difficulty", ["", "insane", None, 2])
def test_invalid_difficulties_are_rejected(difficulty):
    with pytest.raises(InvalidScoreError):
        validate_result(10, "classic", difficulty)


def test_max_score_boundary():
    validate_result(100, "classic", "easy", max_score=100)
    with pytest.raises(InvalidScoreError):
        validate_result(101, "classic", "easy", max_score=100)


# ---------------------------------------------------------- submit_score
def test_submit_score_saves_and_updates_the_leaderboard(db_path, alice):
    score_id = submit_score(alice, 70, "survival", "hard", actor_id=alice,
                            db_path=db_path)
    assert get_scores_for_user(alice, db_path=db_path)[0]["id"] == score_id
    assert get_leaderboard(db_path=db_path)[0]["score"] == 70


def test_a_player_cannot_save_a_score_for_someone_else(db_path, alice, bob):
    with pytest.raises(ScoreAccessError):
        submit_score(bob, 999, "classic", "easy", actor_id=alice,
                     db_path=db_path)
    assert get_scores_for_user(bob, db_path=db_path) == []


def test_rejected_scores_are_not_stored(db_path, alice):
    for args in ((-5, "classic", "easy"), (10, "cheat", "easy"),
                 (10, "classic", "nightmare")):
        with pytest.raises(InvalidScoreError):
            submit_score(alice, *args, actor_id=alice, db_path=db_path)
    assert get_scores_for_user(alice, db_path=db_path) == []
    assert get_leaderboard(db_path=db_path) == []


def test_admin_configured_maximum_is_enforced(db_path, alice):
    root = create_user("root", "h", db_path)
    admin_repo.add_admin(root, db_path=db_path)
    AdminService(root, db_path=db_path).set_config("score.max_per_game", 500)
    submit_score(alice, 500, "classic", "easy", actor_id=alice,
                 db_path=db_path)
    with pytest.raises(InvalidScoreError):
        submit_score(alice, 501, "classic", "easy", actor_id=alice,
                     db_path=db_path)


# ------------------------------------------------------- database guards
def test_saved_scores_cannot_be_edited(db_path, alice):
    score_id = save_score(alice, 40, "classic", "easy", db_path)
    connection = raw(db_path)
    try:
        with pytest.raises(sqlite3.IntegrityError, match="cannot be mod"):
            connection.execute("UPDATE scores SET score = 99999 WHERE id = ?",
                               (score_id,))
    finally:
        connection.close()
    assert get_scores_for_user(alice, db_path=db_path)[0]["score"] == 40


def test_leaderboard_cannot_be_edited_to_a_fake_score(db_path, alice):
    save_score(alice, 40, "classic", "easy", db_path)
    connection = raw(db_path)
    try:
        for sql in ("UPDATE leaderboard SET best_score = 99999",
                    "UPDATE leaderboard SET mode = 'survival'",
                    "UPDATE leaderboard SET user_id = 2"):
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute(sql)
    finally:
        connection.close()
    assert get_leaderboard(db_path=db_path)[0]["score"] == 40


def test_leaderboard_rows_cannot_be_forged(db_path, alice, bob):
    real = save_score(alice, 10, "classic", "easy", db_path)
    connection = raw(db_path)
    try:
        with pytest.raises(sqlite3.IntegrityError, match="must match"):
            connection.execute(
                "INSERT INTO leaderboard (user_id, best_score, mode, "
                "difficulty, achieved_at, score_id) "
                "VALUES (?, 99999, 'classic', 'easy', 'x', ?)",
                (bob, real))
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO leaderboard (user_id, best_score, mode, "
                "difficulty, achieved_at, score_id) "
                "VALUES (?, 10, 'classic', 'easy', 'x', ?)", (bob, real))
    finally:
        connection.close()
    assert [e["username"] for e in get_leaderboard(db_path=db_path)] == [
        "alice"]


def test_normal_play_still_works_with_the_guards(db_path, alice):
    for value in (20, 50, 30, 50, 5):         # better, worse and tied scores
        save_score(alice, value, "classic", "easy", db_path)
    board = get_leaderboard(db_path=db_path)
    assert len(board) == 1 and board[0]["score"] == 50
    assert len(get_scores_for_user(alice, db_path=db_path)) == 5


def test_guards_are_reinstalled_when_the_database_is_opened(db_path, alice):
    score_id = save_score(alice, 40, "classic", "easy", db_path)
    connection = raw(db_path)
    try:
        with connection:
            connection.execute("DROP TRIGGER scores_are_immutable")
            connection.execute("UPDATE scores SET score = 1 WHERE id = ?",
                               (score_id,))
    finally:
        connection.close()
    initialize_database(db_path)               # what the game does at start
    connection = raw(db_path)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("UPDATE scores SET score = 2")
    finally:
        connection.close()


# ----------------------------------------------------- verify and rebuild
def tamper(db_path, *statements):
    """Edit the database the way someone with a SQLite tool could."""
    connection = raw(db_path)
    try:
        with connection:
            for trigger in ("scores_are_immutable",
                            "leaderboard_matches_score_on_insert",
                            "leaderboard_matches_score_on_update"):
                connection.execute("DROP TRIGGER IF EXISTS %s" % trigger)
            for sql in statements:
                connection.execute(sql)
    finally:
        connection.close()


def test_clean_database_verifies_ok(db_path, alice, bob):
    save_score(alice, 40, "classic", "easy", db_path)
    save_score(bob, 60, "survival", "hard", db_path)
    report = verify_integrity(db_path)
    assert report.ok and report.problems == []
    assert report.scores_checked == 2 and report.leaderboard_rows == 2


def test_empty_database_verifies_ok(db_path):
    assert verify_integrity(db_path).ok


def test_tampered_leaderboard_is_detected(db_path, alice):
    save_score(alice, 40, "classic", "easy", db_path)
    tamper(db_path, "UPDATE leaderboard SET best_score = 99999")
    kinds = {p["kind"] for p in verify_integrity(db_path).problems}
    assert "leaderboard_mismatch" in kinds


def test_tampered_score_value_is_detected(db_path, alice):
    save_score(alice, 40, "classic", "easy", db_path)
    tamper(db_path, "UPDATE scores SET score = 7777")
    kinds = {p["kind"] for p in verify_integrity(db_path).problems}
    assert "leaderboard_mismatch" in kinds


def test_leaderboard_that_is_not_the_best_is_detected(db_path, alice):
    low = save_score(alice, 10, "classic", "easy", db_path)
    save_score(alice, 90, "classic", "easy", db_path)
    tamper(db_path,
           "DELETE FROM leaderboard",
           "INSERT INTO leaderboard (user_id, best_score, mode, difficulty,"
           " achieved_at, score_id) SELECT user_id, score, mode, difficulty,"
           " created_at, id FROM scores WHERE id = %d" % low)
    kinds = {p["kind"] for p in verify_integrity(db_path).problems}
    assert kinds == {"leaderboard_not_best"}


def test_missing_leaderboard_entry_is_detected(db_path, alice):
    save_score(alice, 40, "classic", "easy", db_path)
    tamper(db_path, "DELETE FROM leaderboard")
    kinds = {p["kind"] for p in verify_integrity(db_path).problems}
    assert kinds == {"missing_leaderboard_entry"}


def test_invalid_stored_score_is_detected(db_path, alice):
    tamper(db_path,
           "INSERT INTO scores (user_id, score, mode, difficulty) "
           "VALUES (%d, 5, 'cheat-mode', 'easy')" % alice)
    kinds = {p["kind"] for p in verify_integrity(db_path).problems}
    assert "invalid_score" in kinds


def test_rebuild_repairs_the_leaderboard(db_path, alice, bob):
    save_score(alice, 10, "classic", "easy", db_path)
    save_score(alice, 90, "survival", "hard", db_path)
    save_score(bob, 55, "classic", "medium", db_path)
    tamper(db_path, "UPDATE leaderboard SET best_score = 1")
    assert not verify_integrity(db_path).ok

    assert integrity.rebuild_leaderboard(db_path) == 2

    assert verify_integrity(db_path).ok
    board = get_leaderboard(db_path=db_path)
    assert [(e["username"], e["score"]) for e in board] == [
        ("alice", 90), ("bob", 55)]


def test_rebuild_keeps_the_first_of_tied_scores(db_path, alice):
    first = save_score(alice, 50, "classic", "easy", db_path)
    save_score(alice, 50, "survival", "hard", db_path)
    integrity.rebuild_leaderboard(db_path)
    assert get_leaderboard(db_path=db_path)[0]["mode"] == "classic"
    assert first == get_scores_for_user(alice, db_path=db_path)[-1]["id"]


# ------------------------------------------------------------ admin tools
@pytest.fixture()
def admin_service(db_path):
    root = create_user("root", "h", db_path)
    admin_repo.add_admin(root, db_path=db_path)
    return AdminService(root, db_path=db_path)


def test_admin_can_check_and_repair(db_path, alice, admin_service):
    save_score(alice, 40, "classic", "easy", db_path)
    assert admin_service.check_data_integrity().ok
    tamper(db_path, "UPDATE leaderboard SET best_score = 1")
    assert not admin_service.check_data_integrity().ok
    assert admin_service.rebuild_leaderboard() == 1
    assert admin_service.check_data_integrity().ok
    actions = [e["action"] for e in admin_service.audit_log()]
    assert "rebuild_leaderboard" in actions
    assert actions.count("check_integrity") == 3


def test_players_cannot_run_the_integrity_tools(db_path, alice):
    service = AdminService(alice, db_path=db_path)
    with pytest.raises(PermissionDeniedError):
        service.check_data_integrity()
    with pytest.raises(PermissionDeniedError):
        service.rebuild_leaderboard()


# -------------------------------------------------- the player's session
def finished_state(score, mode="classic", difficulty="medium"):
    state = GameState(width=10, height=10, mode=mode, difficulty=difficulty)
    state.score = score
    return state


@pytest.fixture()
def session(db_path, alice):
    guarded = GuardedSession(db_path=db_path)
    guarded.login("alice")
    return guarded


def test_session_saves_valid_results(session, db_path):
    assert session.finish_game(finished_state(60)) is True
    assert get_leaderboard(db_path=db_path)[0]["score"] == 60


def test_session_refuses_impossible_results(session, db_path):
    for bad in (-10, 10**9):
        assert session.save_result(finished_state(bad)) is None
    assert session.save_result(finished_state(10, mode="hax")) is None
    assert get_scores_for_user(session.user_id, db_path=db_path) == []


def test_session_offers_no_way_to_edit_saved_scores():
    public = {name for name in dir(GuardedSession) if not name.startswith("_")}
    editors = {name for name in public
               if any(word in name for word in ("update", "edit", "delete",
                                                "set_score", "modify"))}
    assert editors == set()


# -------------------------------------------------------- Flask backend
def test_flask_scores_cannot_be_updated(tmp_path):
    from app import create_app
    flask_app = create_app({"TESTING": True, "SECRET_KEY": "t",
                            "DATABASE": str(tmp_path / "f.sqlite")})
    client = flask_app.test_client()
    client.post("/api/auth/register", json={
        "username": "alice_1", "email": "a@example.com",
        "password": "Password1"})
    client.post("/api/auth/login",
                json={"username": "alice_1", "password": "Password1"})
    client.post("/api/scores", json={"food_eaten": 2, "duration_seconds": 5})

    connection = sqlite3.connect(flask_app.config["DATABASE"])
    try:
        with pytest.raises(sqlite3.IntegrityError, match="cannot be mod"):
            connection.execute("UPDATE scores SET score = 99999")
    finally:
        connection.close()
    assert client.get("/api/scores/me").get_json()["best"] == 30
