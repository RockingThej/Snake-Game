"""S2-17: security test suite (STP section 5.1, Appendix A).

One section per test case, written from the outside (as an attacker or a
curious player would try things) and spanning the desktop modules and the
Flask backend. Unit-level details live in the per-module test files.

    TC-SEC-001  Password storage          SNAKE-SR-001
    TC-SEC-002  Admin authorization       SNAKE-SR-002
    TC-SEC-003  Input validation          SNAKE-SR-003
    TC-SEC-004  Score/leaderboard integrity   SNAKE-SR-004
    TC-SEC-005  Session termination       SNAKE-SR-005
    TC-AUTH-003 Logout                    SNAKE-F-004
    TC-NF-REL-001 Score persistence       SNAKE-NF-003
"""
import inspect
import logging
import sqlite3

import bcrypt
import pytest

from admin import AdminService, PermissionDeniedError
from app import create_app
from auth import DbAuth
from auth.guarded_session import GuardedSession, NotAuthenticatedError
from auth.secure_auth import SecureAuth
from auth.session_manager import SessionManager
from auth.session_policy import SessionPolicy
from db import (
    create_user,
    get_leaderboard,
    get_scores_for_user,
    get_table_names,
    get_user_by_username,
    initialize_database,
    save_score,
)
from db import admin_repository as admin_repo
from engine.game_state import GameState
from scoring.integrity import ScoreAccessError, submit_score, verify_integrity

PASSWORD = "Tr0ub4dor&3-horse"


# ---------------------------------------------------------------- helpers
@pytest.fixture()
def db_path(tmp_path):
    path = str(tmp_path / "security.sqlite3")
    initialize_database(path)
    return path


@pytest.fixture()
def admin_id(db_path):
    user_id = create_user("root", "placeholder-hash", db_path)
    admin_repo.add_admin(user_id, db_path=db_path)
    return user_id


def register(db_path, username, password=PASSWORD):
    SecureAuth(db_path=db_path).register(username, password)
    return get_user_by_username(username, db_path=db_path)["id"]


def finished_state(score=40):
    state = GameState(width=10, height=10)
    state.score = score
    return state


class FakeClock:
    def __init__(self):
        self.now = 5_000_000.0

    def __call__(self):
        return self.now


@pytest.fixture()
def flask_app(tmp_path):
    return create_app({"TESTING": True, "SECRET_KEY": "security-test",
                       "DATABASE": str(tmp_path / "flask.sqlite")})


@pytest.fixture()
def api(flask_app):
    return flask_app.test_client()


FLASK_USER = {"username": "mallory_1", "email": "m@example.com",
              "password": PASSWORD}


def flask_login(client):
    client.post("/api/auth/register", json=FLASK_USER)
    return client.post("/api/auth/login", json={
        "username": FLASK_USER["username"],
        "password": FLASK_USER["password"]})


# ===================================================== TC-SEC-001 passwords
class TestPasswordStorage:
    """TC-SEC-001: passwords are hashed one-way; plaintext never stored."""

    def test_desktop_stores_a_bcrypt_hash(self, db_path):
        register(db_path, "alice")
        stored = get_user_by_username("alice", db_path=db_path)[
            "password_hash"]
        assert stored != PASSWORD
        assert stored.startswith("$2")
        assert bcrypt.checkpw(PASSWORD.encode(), stored.encode())

    def test_plaintext_is_nowhere_in_the_database_file(self, db_path):
        register(db_path, "alice")
        with open(db_path, "rb") as handle:
            assert PASSWORD.encode() not in handle.read()

    def test_the_same_password_gets_different_hashes(self, db_path):
        register(db_path, "alice")
        register(db_path, "bobby")
        hashes = {get_user_by_username(name, db_path=db_path)[
            "password_hash"] for name in ("alice", "bobby")}
        assert len(hashes) == 2

    def test_admin_password_reset_also_stores_a_hash(self, db_path,
                                                     admin_id):
        user_id = register(db_path, "alice")
        AdminService(admin_id, db_path=db_path).reset_password(
            user_id, "An0ther-Secret!")
        stored = get_user_by_username("alice", db_path=db_path)[
            "password_hash"]
        assert stored.startswith("$2") and "An0ther" not in stored
        with open(db_path, "rb") as handle:
            assert b"An0ther-Secret!" not in handle.read()

    def test_passwords_never_reach_the_logs(self, db_path, admin_id, caplog):
        with caplog.at_level(logging.DEBUG):
            user_id = register(db_path, "alice")
            SecureAuth(db_path=db_path).login("alice", PASSWORD)
            SecureAuth(db_path=db_path).login("alice", "wrong-Pass-99")
            AdminService(admin_id, db_path=db_path).reset_password(
                user_id, "An0ther-Secret!")
        assert PASSWORD not in caplog.text
        assert "wrong-Pass-99" not in caplog.text
        assert "An0ther-Secret!" not in caplog.text

    def test_flask_stores_a_bcrypt_hash_and_never_returns_it(
            self, flask_app, api):
        reply = api.post("/api/auth/register", json=FLASK_USER)
        assert PASSWORD not in reply.get_data(as_text=True)
        api.post("/api/auth/login", json={
            "username": FLASK_USER["username"], "password": PASSWORD})
        me = api.get("/api/auth/me").get_data(as_text=True)
        assert "hash" not in me and PASSWORD not in me

        connection = sqlite3.connect(flask_app.config["DATABASE"])
        try:
            stored = connection.execute(
                "SELECT password_hash FROM users").fetchone()[0]
        finally:
            connection.close()
        assert bytes(stored).startswith(b"$2")
        with open(flask_app.config["DATABASE"], "rb") as handle:
            assert PASSWORD.encode() not in handle.read()


# ================================================ TC-SEC-002 administration
def _public_admin_methods():
    return sorted(
        name for name, member in inspect.getmembers(
            AdminService, inspect.isfunction)
        if not name.startswith("_"))


def _call_with_dummy_arguments(service, name):
    method = getattr(service, name)
    required = [
        p for p in inspect.signature(method).parameters.values()
        if p.default is inspect.Parameter.empty]
    return method(*([1] * len(required)))


class TestAdminAuthorization:
    """TC-SEC-002: only authenticated, authorised administrators."""

    def test_the_list_of_admin_functions_is_not_empty(self):
        assert len(_public_admin_methods()) >= 15

    @pytest.mark.parametrize("name", _public_admin_methods())
    def test_a_normal_player_is_refused_by_every_admin_function(
            self, db_path, admin_id, name):
        player = create_user("player", "h", db_path)
        service = AdminService(player, db_path=db_path)
        with pytest.raises(PermissionDeniedError):
            _call_with_dummy_arguments(service, name)

    @pytest.mark.parametrize("name", _public_admin_methods())
    def test_a_logged_out_admin_is_refused_by_every_admin_function(
            self, db_path, admin_id, name):
        session = GuardedSession(db_path=db_path)
        session.login("root")
        service = AdminService.from_session(session)
        session.logout()
        with pytest.raises(PermissionDeniedError):
            _call_with_dummy_arguments(service, name)

    def test_nobody_logged_in_cannot_open_the_admin_module(self, db_path):
        with pytest.raises(NotAuthenticatedError):
            AdminService.from_session(GuardedSession(db_path=db_path))

    def test_a_player_cannot_make_themselves_admin(self, db_path, admin_id):
        player = create_user("player", "h", db_path)
        with pytest.raises(PermissionDeniedError):
            AdminService(player, db_path=db_path).grant_admin(player)
        assert not admin_repo.is_admin(player, db_path=db_path)

    def test_there_is_no_admin_flag_on_the_player_session(self, db_path):
        session = GuardedSession(db_path=db_path)
        assert not any("admin" in name.lower() for name in vars(session))

    def test_a_disabled_administrator_cannot_log_in(self, db_path,
                                                    admin_id):
        boss = register(db_path, "boss")
        admin_repo.add_admin(boss, db_path=db_path)
        AdminService(admin_id, db_path=db_path).set_user_disabled(boss, True)
        assert SecureAuth(db_path=db_path).login("boss", PASSWORD) is False

    def test_search_text_is_never_run_as_sql(self, db_path, admin_id):
        create_user("victim", "h", db_path)
        service = AdminService(admin_id, db_path=db_path)
        assert service.list_users(search="' OR 1=1 --") == []
        assert service.list_users(search="x'; DROP TABLE users;--") == []
        assert "users" in get_table_names(db_path)


# ================================================= TC-SEC-003 input handling
class TestInputValidation:
    """TC-SEC-003: valid, malformed and unexpected input."""

    @pytest.mark.parametrize("username", [
        "", "ab", "a" * 33, "bad name", "new\nline", "nul\x00byte",
        "x'; DROP TABLE users;--", "<script>alert(1)</script>", None, 42])
    def test_desktop_registration_rejects_bad_usernames(
            self, db_path, username):
        with pytest.raises(ValueError):
            SecureAuth(db_path=db_path).register(username, PASSWORD)

    @pytest.mark.parametrize("password", [
        "", "short", "p" * 73, "é" * 40, None, 123456])
    def test_desktop_registration_rejects_bad_passwords(
            self, db_path, password):
        with pytest.raises(ValueError):
            SecureAuth(db_path=db_path).register("alice", password)

    def test_a_very_long_login_password_is_refused_not_a_crash(
            self, db_path):
        register(db_path, "alice")
        assert SecureAuth(db_path=db_path).login("alice", "x" * 500) is False
        assert SecureAuth(db_path=db_path).login("alice", None) is False
        assert SecureAuth(db_path=db_path).login(None, PASSWORD) is False

    def test_sql_in_credentials_does_not_touch_the_database(self, db_path):
        register(db_path, "alice")
        auth = SecureAuth(db_path=db_path)
        assert auth.login("alice' OR '1'='1", "anything") is False
        assert auth.login("alice", "' OR '1'='1") is False
        # even the unhardened service stores such text as plain data
        DbAuth(db_path=db_path).register("x'; DROP TABLE users;--", "secret1")
        assert get_table_names(db_path) == ("users", "scores", "leaderboard")

    @pytest.mark.parametrize("path", ["/api/auth/register",
                                      "/api/auth/login", "/api/scores"])
    @pytest.mark.parametrize("body", [[1, 2], "text", 5, True])
    def test_flask_rejects_json_that_is_not_an_object(self, api, path, body):
        flask_login(api)
        assert api.post(path, json=body).status_code == 400

    @pytest.mark.parametrize("path", ["/api/auth/register",
                                      "/api/auth/login", "/api/scores"])
    def test_flask_rejects_broken_or_missing_json(self, api, path):
        flask_login(api)
        assert api.post(path, data="{not json",
                        content_type="application/json").status_code == 400
        assert api.post(path).status_code in (400, 415)

    @pytest.mark.parametrize("field,value", [
        ("username", "x'; DROP TABLE users;--"), ("username", "a" * 500),
        ("email", "not-an-email"), ("email", "a@b.c" + "x" * 300),
        ("password", "weak"), ("password", "A1" + "b" * 100)])
    def test_flask_rejects_bad_registration_fields(self, api, field, value):
        body = {**FLASK_USER, field: value}
        assert api.post("/api/auth/register", json=body).status_code == 400

    def test_flask_refuses_huge_request_bodies(self, api):
        body = {**FLASK_USER, "username": "u" * 200_000}
        assert api.post("/api/auth/register", json=body).status_code == 413

    @pytest.mark.parametrize("payload", [
        {"food_eaten": "3", "duration_seconds": 5},
        {"food_eaten": -1, "duration_seconds": 5},
        {"food_eaten": 1.5, "duration_seconds": 5},
        {"food_eaten": True, "duration_seconds": 5},
        {"food_eaten": 1, "duration_seconds": 5, "difficulty": "x'--"},
        {"food_eaten": 10**12, "duration_seconds": 5},
        {}])
    def test_flask_rejects_bad_score_submissions(self, api, payload):
        flask_login(api)
        assert api.post("/api/scores", json=payload).status_code == 400
        assert api.get("/api/scores/me").get_json()["scores"] == []

    @pytest.mark.parametrize("limit", ["abc", "0", "-5", "101", "1;DROP"])
    def test_flask_rejects_bad_leaderboard_limits(self, api, limit):
        assert api.get("/api/leaderboard?limit=" + limit).status_code == 400

    @pytest.mark.parametrize("args", [
        (-1, "classic", "easy"), (1.5, "classic", "easy"),
        (True, "classic", "easy"), (5, "classic'; --", "easy"),
        (5, "classic", "godlike")])
    def test_desktop_scores_with_bad_values_are_refused(self, db_path, args):
        user_id = create_user("alice", "h", db_path)
        with pytest.raises(ValueError):
            submit_score(user_id, *args, actor_id=user_id, db_path=db_path)
        assert get_scores_for_user(user_id, db_path=db_path) == []


# ==================================== TC-SEC-004 score/leaderboard integrity
class TestScoreIntegrity:
    """TC-SEC-004: normal player interfaces cannot alter stored records."""

    def test_a_player_cannot_save_a_score_for_another_player(self, db_path):
        alice = create_user("alice", "h", db_path)
        bob = create_user("bob", "h", db_path)
        with pytest.raises(ScoreAccessError):
            submit_score(bob, 500, "classic", "easy", actor_id=alice,
                         db_path=db_path)
        assert get_leaderboard(db_path=db_path) == []

    def test_the_game_session_only_ever_saves_for_its_own_player(
            self, db_path):
        register(db_path, "alice")
        bob = register(db_path, "bobby")
        session = GuardedSession(db_path=db_path)
        session.login("alice")
        session.finish_game(finished_state(60))
        assert get_scores_for_user(bob, db_path=db_path) == []

    @pytest.mark.parametrize("sql", [
        "UPDATE scores SET score = 999999",
        "UPDATE leaderboard SET best_score = 999999",
        "UPDATE leaderboard SET user_id = 2",
        "INSERT INTO leaderboard (user_id, best_score, mode, difficulty, "
        "achieved_at, score_id) VALUES (2, 999999, 'classic', 'easy', "
        "'x', 1)"])
    def test_direct_edits_of_stored_records_are_refused(self, db_path, sql):
        alice = create_user("alice", "h", db_path)
        create_user("bob", "h", db_path)
        save_score(alice, 40, "classic", "easy", db_path)
        connection = sqlite3.connect(db_path)
        try:
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute(sql)
        finally:
            connection.close()
        assert get_leaderboard(db_path=db_path)[0]["score"] == 40
        assert verify_integrity(db_path).ok

    def test_two_players_playing_leaves_consistent_records(self, db_path):
        register(db_path, "alice")
        register(db_path, "bobby")
        for name, scores in (("alice", (30, 80, 50)), ("bobby", (70, 20))):
            session = GuardedSession(db_path=db_path)
            session.login(name)
            for value in scores:
                assert session.finish_game(finished_state(value))
            session.logout()
        board = {e["username"]: e["score"] for e in get_leaderboard(
            db_path=db_path)}
        assert board == {"alice": 80, "bobby": 70}
        assert verify_integrity(db_path).ok

    @pytest.mark.parametrize("method", ["put", "patch", "delete"])
    @pytest.mark.parametrize("path", ["/api/scores", "/api/scores/me",
                                      "/api/leaderboard"])
    def test_flask_offers_no_way_to_change_or_delete_records(
            self, api, method, path):
        flask_login(api)
        assert getattr(api, method)(path, json={"score": 1}
                                    ).status_code == 405

    def test_flask_leaderboard_is_read_only(self, api):
        assert api.post("/api/leaderboard", json={"score": 1}
                        ).status_code == 405

    def test_flask_ignores_a_client_supplied_score(self, api):
        flask_login(api)
        reply = api.post("/api/scores", json={
            "food_eaten": 1, "duration_seconds": 0, "score": 999999,
            "best": 999999, "user_id": 99})
        assert reply.get_json()["score"] == 15
        assert api.get("/api/scores/me").get_json()["best"] == 15

    def test_flask_players_only_see_their_own_scores(self, flask_app):
        first, second = flask_app.test_client(), flask_app.test_client()
        flask_login(first)
        first.post("/api/scores", json={"food_eaten": 9,
                                        "duration_seconds": 1})
        second.post("/api/auth/register", json={
            "username": "other_2", "email": "o@example.com",
            "password": PASSWORD})
        second.post("/api/auth/login", json={"username": "other_2",
                                             "password": PASSWORD})
        assert second.get("/api/scores/me").get_json()["scores"] == []

    def test_flask_anonymous_users_cannot_submit_scores(self, api):
        reply = api.post("/api/scores", json={"food_eaten": 1,
                                              "duration_seconds": 1})
        assert reply.status_code == 401


# ============================== TC-SEC-005 / TC-AUTH-003 session termination
class TestSessionTermination:
    """TC-SEC-005 and TC-AUTH-003: protected functionality after logout."""

    def test_after_logout_nothing_protected_works_on_the_desktop(
            self, db_path, admin_id):
        user_id = register(db_path, "alice")
        session = GuardedSession(db_path=db_path)
        session.login("alice")
        token = session.token
        assert session.finish_game(finished_state(10)) is True

        session.logout()

        assert session.logged_in is False
        assert session.save_result(finished_state(99)) is None
        with pytest.raises(NotAuthenticatedError):
            session.require_login()
        assert not SessionManager(db_path).is_active(token)
        assert len(get_scores_for_user(user_id, db_path=db_path)) == 1

    def test_an_old_token_cannot_be_revived(self, db_path):
        register(db_path, "alice")
        session = GuardedSession(db_path=db_path)
        session.login("alice")
        old_token = session.token
        session.logout()
        session.login("alice")                      # a brand-new login
        session.token = old_token                   # attacker replays old
        assert session.logged_in is False

    def test_idle_sessions_end_by_themselves(self, db_path, admin_id):
        clock = FakeClock()
        manager = SessionManager(
            db_path, clock=clock,
            policy=SessionPolicy(idle_timeout=300, absolute_timeout=3600))
        session = GuardedSession(db_path=db_path, manager=manager)
        session.login("root")
        service = AdminService.from_session(session)
        assert service.list_users()
        clock.now += 301
        with pytest.raises(PermissionDeniedError):
            service.list_users()
        assert session.save_result(finished_state(5)) is None

    def test_disabling_an_account_ends_its_open_session(self, db_path,
                                                        admin_id):
        user_id = register(db_path, "alice")
        session = GuardedSession(db_path=db_path)
        session.login("alice")
        AdminService(admin_id, db_path=db_path).set_user_disabled(
            user_id, True)
        assert session.logged_in is False
        assert SecureAuth(db_path=db_path).login("alice", PASSWORD) is False

    def test_a_password_reset_ends_open_sessions(self, db_path, admin_id):
        user_id = register(db_path, "alice")
        session = GuardedSession(db_path=db_path)
        session.login("alice")
        AdminService(admin_id, db_path=db_path).reset_password(
            user_id, "Brand-New-Pass1")
        assert session.logged_in is False

    def test_logout_everywhere_ends_every_window(self, db_path):
        register(db_path, "alice")
        first, second = (GuardedSession(db_path=db_path) for _ in range(2))
        first.login("alice")
        second.login("alice")
        first.logout_everywhere()
        assert not first.logged_in and not second.logged_in

    def test_flask_a_copied_cookie_stops_working_after_logout(
            self, flask_app, api):
        flask_login(api)
        stolen = api.get_cookie("session").value
        api.post("/api/auth/logout")
        attacker = flask_app.test_client()
        attacker.set_cookie("session", stolen)
        assert attacker.get("/api/auth/me").status_code == 401
        assert attacker.post("/api/scores", json={
            "food_eaten": 1, "duration_seconds": 1}).status_code == 401

    def test_flask_logout_everywhere_and_forged_ids(self, flask_app, api):
        flask_login(api)
        other = flask_app.test_client()
        other.post("/api/auth/login", json={
            "username": FLASK_USER["username"], "password": PASSWORD})
        api.post("/api/auth/logout-all")
        assert other.get("/api/auth/me").status_code == 401
        with api.session_transaction() as flask_session:
            flask_session["sid"] = "guess-a-session-id"
        assert api.get("/api/auth/me").status_code == 401

    def test_flask_idle_timeout(self, tmp_path):
        clock = FakeClock()
        app = create_app({
            "TESTING": True, "SECRET_KEY": "t",
            "DATABASE": str(tmp_path / "idle.sqlite"),
            "SESSION_CLOCK": clock, "SESSION_IDLE_SECONDS": 300,
            "SESSION_ABSOLUTE_SECONDS": 3600})
        client = app.test_client()
        flask_login(client)
        clock.now += 301
        assert client.get("/api/auth/me").status_code == 401


# ================================================ TC-NF-REL-001 persistence
class TestScorePersistence:
    """TC-NF-REL-001: a stored score is retrieved unchanged, every time."""

    def test_repeated_retrieval_matches_the_stored_score(self, db_path):
        alice = create_user("alice", "h", db_path)
        save_score(alice, 123, "survival", "hard", db_path)
        snapshots = []
        for _ in range(20):
            initialize_database(db_path)           # as on every game start
            snapshots.append((
                [(r["score"], r["mode"], r["difficulty"])
                 for r in get_scores_for_user(alice, db_path=db_path)],
                [(r["score"], r["mode"], r["difficulty"])
                 for r in get_leaderboard(db_path=db_path)]))
        assert all(s == snapshots[0] for s in snapshots)
        assert snapshots[0][0] == [(123, "survival", "hard")]
        assert verify_integrity(db_path).ok

    def test_scores_survive_logout_and_a_new_login(self, db_path):
        user_id = register(db_path, "alice")
        for _ in range(2):
            session = GuardedSession(db_path=db_path)
            session.login("alice")
            session.finish_game(finished_state(25))
            session.logout()
        assert len(get_scores_for_user(user_id, db_path=db_path)) == 2
