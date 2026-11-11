"""S2-14: Administration module (SRS 7.2, SNAKE-SR-002, TC-SEC-002)."""
import pytest

from admin import AdminError, AdminService, PermissionDeniedError
from admin import config as game_config
from auth import DbAuth
from auth.guarded_session import GuardedSession, NotAuthenticatedError
from auth.secure_auth import SecureAuth
from auth.session_manager import SessionManager
from auth.session_policy import SessionPolicy
from db import (
    create_user,
    get_leaderboard,
    get_scores_for_user,
    get_user_by_username,
    initialize_database,
    save_score,
)
from db import admin_repository as repo
from modes.difficulty import DifficultyManager


@pytest.fixture()
def db_path(tmp_path):
    path = str(tmp_path / "admin.sqlite3")
    initialize_database(path)
    return path


@pytest.fixture()
def root(db_path):
    user_id = create_user("root", "hash-root", db_path)
    repo.add_admin(user_id, db_path=db_path)
    return user_id


@pytest.fixture()
def alice(db_path):
    return create_user("alice", "hash-alice", db_path)


@pytest.fixture()
def bob(db_path):
    return create_user("bob", "hash-bob", db_path)


@pytest.fixture()
def service(db_path, root):
    return AdminService(root, db_path=db_path)


# ---------------------------------------------------------- authorisation
ADMIN_CALLS = {
    "list_users": lambda s: s.list_users(),
    "get_user": lambda s: s.get_user(1),
    "set_user_disabled": lambda s: s.set_user_disabled(1, True),
    "reset_password": lambda s: s.reset_password(1, "newsecret1"),
    "delete_user": lambda s: s.delete_user(1),
    "grant_admin": lambda s: s.grant_admin(1),
    "revoke_admin": lambda s: s.revoke_admin(1),
    "get_leaderboard": lambda s: s.get_leaderboard(),
    "list_user_scores": lambda s: s.list_user_scores(1),
    "delete_score": lambda s: s.delete_score(1),
    "reset_user_scores": lambda s: s.reset_user_scores(1),
    "game_statistics": lambda s: s.game_statistics(),
    "player_statistics": lambda s: s.player_statistics(1),
    "get_config": lambda s: s.get_config(),
    "set_config": lambda s: s.set_config("powerup.duration_s", 5),
    "reset_config": lambda s: s.reset_config("powerup.duration_s"),
    "audit_log": lambda s: s.audit_log(),
}


@pytest.mark.parametrize("name", sorted(ADMIN_CALLS))
def test_players_cannot_use_any_admin_function(db_path, root, alice, name):
    player_service = AdminService(alice, db_path=db_path)
    with pytest.raises(PermissionDeniedError):
        ADMIN_CALLS[name](player_service)


def test_unknown_actor_is_denied(db_path, root):
    with pytest.raises(PermissionDeniedError):
        AdminService(99999, db_path=db_path).list_users()


def test_denied_calls_change_nothing(db_path, root, alice, bob):
    with pytest.raises(PermissionDeniedError):
        AdminService(alice, db_path=db_path).delete_user(bob)
    assert get_user_by_username("bob", db_path=db_path) is not None
    assert AdminService(root, db_path=db_path).audit_log() == []


def test_admin_loses_access_as_soon_as_rights_are_removed(
        db_path, service, root):
    other = create_user("other", "hash-o", db_path)
    repo.add_admin(other, db_path=db_path)
    assert service.list_users()
    repo.remove_admin(root, db_path=db_path)
    with pytest.raises(PermissionDeniedError):
        service.list_users()


# ------------------------------------------------------- session binding
@pytest.fixture()
def admin_session(db_path, root):
    session = GuardedSession(db_path=db_path)
    session.login("root")
    return session


def test_from_session_requires_login(db_path, root):
    session = GuardedSession(db_path=db_path)
    with pytest.raises(NotAuthenticatedError):
        AdminService.from_session(session)


def test_admin_functions_lock_after_logout(admin_session):
    service = AdminService.from_session(admin_session)
    assert service.list_users()
    admin_session.logout()
    with pytest.raises(PermissionDeniedError):
        service.list_users()
    with pytest.raises(PermissionDeniedError):
        service.set_config("powerup.duration_s", 5)


def test_admin_functions_lock_when_the_session_times_out(db_path, root):
    now = [1000.0]
    manager = SessionManager(
        db_path, policy=SessionPolicy(idle_timeout=60, absolute_timeout=600),
        clock=lambda: now[0])
    session = GuardedSession(db_path=db_path, manager=manager)
    session.login("root")
    service = AdminService.from_session(session)
    assert service.list_users()
    now[0] += 61
    with pytest.raises(PermissionDeniedError):
        service.list_users()


def test_player_session_cannot_become_admin(db_path, root, alice):
    session = GuardedSession(db_path=db_path)
    session.login("alice")
    with pytest.raises(PermissionDeniedError):
        AdminService.from_session(session).list_users()


def test_service_rejects_a_session_of_another_user(db_path, root, alice):
    session = GuardedSession(db_path=db_path)
    session.login("alice")
    service = AdminService(root, db_path=db_path, session=session)
    with pytest.raises(PermissionDeniedError):
        service.list_users()


# ------------------------------------------------------------- view users
def test_list_users_shows_status_but_never_password_hashes(
        service, alice, db_path):
    save_score(alice, 70, "classic", "easy", db_path)
    users = {user["username"]: user for user in service.list_users()}
    assert set(users) == {"root", "alice"}
    assert users["root"]["is_admin"] is True
    assert users["alice"]["is_admin"] is False
    assert users["alice"]["games_played"] == 1
    assert users["alice"]["best_score"] == 70
    assert users["alice"]["disabled"] is False
    assert all("password" not in key for key in users["alice"])
    assert "hash-alice" not in str(users)


def test_list_users_search_paging_and_wildcards(service, db_path):
    for name in ("anna", "annabel", "bert", "100%_real"):
        create_user(name, "h", db_path)
    names = [u["username"] for u in service.list_users(search="ann")]
    assert names == ["anna", "annabel"]
    assert len(service.list_users(limit=2)) == 2
    assert len(service.list_users(limit=2, offset=4)) == 1
    assert [u["username"] for u in service.list_users(search="%")] == [
        "100%_real"]
    assert service.list_users(search="_") == [
        u for u in service.list_users() if "_" in u["username"]]


def test_list_users_rejects_bad_arguments(service):
    for kwargs in ({"limit": 0}, {"limit": "5"}, {"offset": -1},
                   {"search": 5}):
        with pytest.raises(AdminError):
            service.list_users(**kwargs)


def test_get_user_and_unknown_user(service, alice):
    assert service.get_user(alice)["username"] == "alice"
    with pytest.raises(AdminError):
        service.get_user(424242)
    for bad in (None, "1", True, 0):
        with pytest.raises(AdminError):
            service.get_user(bad)


# ----------------------------------------------------------- manage users
def test_disabled_accounts_cannot_log_in(db_path, service):
    DbAuth(db_path=db_path).register("carol", "secret123")
    carol = get_user_by_username("carol", db_path=db_path)["id"]
    auth = SecureAuth(db_path=db_path)
    assert auth.login("carol", "secret123") is True

    service.set_user_disabled(carol, True, reason="cheating")
    assert auth.login("carol", "secret123") is False
    assert service.get_user(carol)["disabled"] is True
    assert service.get_user(carol)["disabled_reason"] == "cheating"

    service.set_user_disabled(carol, False)
    assert auth.login("carol", "secret123") is True


def test_disabling_ends_the_players_sessions(db_path, service, alice):
    manager = SessionManager(db_path)
    token = manager.start(alice)
    service.set_user_disabled(alice, True)
    assert not manager.is_active(token)


def test_secure_auth_rejects_non_text_input(db_path):
    auth = SecureAuth(db_path=db_path)
    assert auth.login(None, "x") is False
    assert auth.login("x", None) is False


def test_guarded_session_uses_secure_auth_by_default(db_path):
    assert isinstance(GuardedSession(db_path=db_path).auth, SecureAuth)


def test_disable_rules(service, root, alice):
    with pytest.raises(AdminError):
        service.set_user_disabled(root, True)           # not yourself
    with pytest.raises(AdminError):
        service.set_user_disabled(alice, "yes")
    with pytest.raises(AdminError):
        service.set_user_disabled(alice, True, reason="x" * 201)
    with pytest.raises(AdminError):
        service.set_user_disabled(424242, True)


def test_reset_password(db_path, service):
    DbAuth(db_path=db_path).register("carol", "oldsecret1")
    carol = get_user_by_username("carol", db_path=db_path)["id"]
    token = SessionManager(db_path).start(carol)

    service.reset_password(carol, "brandnew99")

    auth = DbAuth(db_path=db_path)
    assert auth.login("carol", "brandnew99") is True
    assert auth.login("carol", "oldsecret1") is False
    assert not SessionManager(db_path).is_active(token)
    stored = get_user_by_username("carol", db_path=db_path)["password_hash"]
    assert stored.startswith("$2") and "brandnew99" not in stored


def test_reset_password_rejects_weak_passwords(service, alice):
    for bad in ("short", "", None):
        with pytest.raises(AdminError):
            service.reset_password(alice, bad)


def test_delete_user_removes_everything_of_theirs(db_path, service, alice):
    save_score(alice, 50, "classic", "easy", db_path)
    token = SessionManager(db_path).start(alice)

    service.delete_user(alice)

    assert get_user_by_username("alice", db_path=db_path) is None
    assert get_leaderboard(db_path=db_path) == []
    assert get_scores_for_user(alice, db_path=db_path) == []
    assert not SessionManager(db_path).is_active(token)


def test_cannot_delete_yourself(service, root):
    with pytest.raises(AdminError):
        service.delete_user(root)


def test_grant_and_revoke_admin(db_path, service, alice):
    service.grant_admin(alice)
    assert AdminService(alice, db_path=db_path).list_users()
    with pytest.raises(AdminError):
        service.grant_admin(alice)                      # already admin
    service.revoke_admin(alice)
    with pytest.raises(PermissionDeniedError):
        AdminService(alice, db_path=db_path).list_users()
    with pytest.raises(AdminError):
        service.revoke_admin(alice)                     # not an admin


def test_the_last_admin_cannot_be_removed(service, root):
    with pytest.raises(AdminError):
        service.revoke_admin(root)
    assert service.get_user(root)["is_admin"] is True


# ----------------------------------------------------- leaderboard data
def test_delete_score_recomputes_the_leaderboard(db_path, service, alice):
    save_score(alice, 30, "classic", "easy", db_path)
    best = save_score(alice, 80, "survival", "hard", db_path)
    assert get_leaderboard(db_path=db_path)[0]["score"] == 80

    service.delete_score(best)

    entry = get_leaderboard(db_path=db_path)[0]
    assert entry["score"] == 30 and entry["mode"] == "classic"
    assert len(get_scores_for_user(alice, db_path=db_path)) == 1


def test_delete_a_score_that_is_not_the_best(db_path, service, alice):
    low = save_score(alice, 10, "classic", "easy", db_path)
    save_score(alice, 90, "classic", "easy", db_path)
    service.delete_score(low)
    assert get_leaderboard(db_path=db_path)[0]["score"] == 90


def test_deleting_the_only_score_removes_the_entry(db_path, service, alice):
    only = save_score(alice, 40, "classic", "easy", db_path)
    service.delete_score(only)
    assert get_leaderboard(db_path=db_path) == []


def test_delete_score_keeps_other_players_untouched(
        db_path, service, alice, bob):
    save_score(bob, 55, "classic", "easy", db_path)
    mine = save_score(alice, 40, "classic", "easy", db_path)
    service.delete_score(mine)
    board = get_leaderboard(db_path=db_path)
    assert [(e["username"], e["score"]) for e in board] == [("bob", 55)]


def test_delete_unknown_score(service):
    with pytest.raises(AdminError):
        service.delete_score(424242)
    with pytest.raises(AdminError):
        service.delete_score("1")


def test_reset_user_scores(db_path, service, alice, bob):
    for value in (10, 20, 30):
        save_score(alice, value, "classic", "easy", db_path)
    save_score(bob, 5, "classic", "easy", db_path)
    assert service.reset_user_scores(alice) == 3
    assert get_scores_for_user(alice, db_path=db_path) == []
    assert [e["username"] for e in get_leaderboard(db_path=db_path)] == [
        "bob"]


def test_admin_can_read_leaderboard_and_scores(db_path, service, alice):
    save_score(alice, 33, "classic", "easy", db_path)
    assert service.get_leaderboard()[0]["score"] == 33
    assert service.list_user_scores(alice)[0]["score"] == 33


# ------------------------------------------------------------ statistics
def test_admin_statistics(db_path, service, alice):
    save_score(alice, 60, "classic", "easy", db_path)
    assert service.game_statistics()["total_games"] == 1
    assert service.player_statistics(alice)["best_score"] == 60
    with pytest.raises(AdminError):
        service.player_statistics(424242)


# --------------------------------------------------------- configuration
def test_config_defaults(service):
    config = service.get_config()
    assert config["difficulty.medium.speed_ms"] == 110
    assert set(config) == set(game_config.PARAMETERS)


def test_set_and_reset_config(service):
    service.set_config("powerup.duration_s", 20)
    service.set_config("leaderboard.display_size", "25")   # text from a UI
    config = service.get_config()
    assert config["powerup.duration_s"] == 20
    assert config["leaderboard.display_size"] == 25
    service.reset_config("powerup.duration_s")
    assert service.get_config()["powerup.duration_s"] == 10


@pytest.mark.parametrize("key,value", [
    ("powerup.duration_s", 0), ("powerup.duration_s", 61),
    ("powerup.duration_s", -3), ("powerup.duration_s", 1.5),
    ("powerup.duration_s", True), ("powerup.duration_s", "abc"),
    ("powerup.duration_s", None),
    ("difficulty.hard.speed_ms", 5),
    ("not.a.parameter", 1), ("'; DROP TABLE users;--", 1),
])
def test_invalid_config_is_rejected(service, key, value):
    with pytest.raises(AdminError):
        service.set_config(key, value)


def test_reset_unknown_config(service):
    with pytest.raises(AdminError):
        service.reset_config("nope")


def test_configured_speeds_plug_into_the_difficulty_manager(
        db_path, service):
    service.set_config("difficulty.hard.speed_ms", 50)
    speeds = game_config.get_difficulty_speeds(db_path)
    assert speeds == {"easy": 160, "medium": 110, "hard": 50}
    assert DifficultyManager(speeds_ms=speeds).get_speed_ms("hard") == 50


def test_damaged_stored_config_falls_back_to_default(db_path, service, root):
    repo.set_config_value("powerup.duration_s", "banana", root,
                          db_path=db_path)
    repo.set_config_value("unknown.key", "1", root, db_path=db_path)
    assert service.get_config()["powerup.duration_s"] == 10


# ------------------------------------------------------------- audit log
def test_every_change_is_audited_newest_first(db_path, service, alice):
    service.set_user_disabled(alice, True, reason="spam")
    service.set_config("powerup.duration_s", 15)
    service.grant_admin(alice)
    log = service.audit_log()
    assert [entry["action"] for entry in log] == [
        "grant_admin", "set_config", "disable_user"]
    assert log[0]["actor_name"] == "root"
    assert log[2]["target"] == "user:%d:alice" % alice
    assert log[2]["detail"] == "spam"


def test_audit_log_never_contains_passwords(db_path, service, alice):
    service.reset_password(alice, "SuperSecret42")
    text = str(service.audit_log())
    assert "SuperSecret42" not in text
    assert "$2" not in text


def test_failed_requests_are_not_audited(service):
    with pytest.raises(AdminError):
        service.delete_score(424242)
    assert service.audit_log() == []


def test_audit_entries_survive_deleting_the_actor(db_path, service, root):
    other = create_user("other", "h", db_path)
    repo.add_admin(other, db_path=db_path)
    AdminService(other, db_path=db_path).set_config("powerup.duration_s", 7)
    service.delete_user(other)
    names = [entry["actor_name"] for entry in service.audit_log()]
    assert "other" in names
