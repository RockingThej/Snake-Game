"""S2-13: session termination (SNAKE-F-004, SNAKE-SR-005).

Covers TC-AUTH-003 and TC-SEC-005 for the desktop game.
"""
import sqlite3

import pytest

from auth import DbAuth
from auth.guarded_session import GuardedSession, NotAuthenticatedError
from auth.session_manager import (
    SessionEndedError,
    SessionExpiredError,
    SessionManager,
    SessionNotFoundError,
)
from auth.session_policy import (
    IDLE_TIMEOUT,
    SessionPolicy,
    end_reason,
    hash_token,
)
from db import get_leaderboard, get_user_by_username
from engine.game_state import GameState


class FakeClock:
    def __init__(self, start=1_000_000.0):
        self.now = start

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


@pytest.fixture()
def db_path(tmp_path):
    return str(tmp_path / "sessions.sqlite3")


@pytest.fixture()
def clock():
    return FakeClock()


@pytest.fixture()
def policy():
    return SessionPolicy(idle_timeout=600, absolute_timeout=3600)


@pytest.fixture()
def manager(db_path, clock, policy):
    return SessionManager(db_path, policy=policy, clock=clock)


@pytest.fixture()
def alice_id(db_path):
    DbAuth(db_path=db_path).register("alice", "secret123")
    return get_user_by_username("alice", db_path=db_path)["id"]


# ---------------------------------------------------------------- policy
def test_policy_rejects_bad_values():
    for kwargs in ({"idle_timeout": 0}, {"idle_timeout": -5},
                   {"absolute_timeout": 0}, {"idle_timeout": True},
                   {"idle_timeout": "10"},
                   {"idle_timeout": 100, "absolute_timeout": 50}):
        with pytest.raises(ValueError):
            SessionPolicy(**kwargs)


def test_end_reason_order_logout_beats_timeouts():
    p = SessionPolicy(idle_timeout=10, absolute_timeout=100)
    kwargs = dict(last_seen_at=0, expires_at=100, policy=p)
    assert end_reason(ended_at=None, now=5, **kwargs) is None
    assert end_reason(ended_at=None, now=10, **kwargs) == IDLE_TIMEOUT
    assert end_reason(ended_at=None, now=100, **kwargs) == "expired"
    assert end_reason(ended_at=3, now=200, **kwargs) == "logout"


def test_hash_token_rejects_empty():
    with pytest.raises(ValueError):
        hash_token("")


# --------------------------------------------------------------- manager
def test_start_and_validate(manager, alice_id):
    token = manager.start(alice_id)
    info = manager.validate(token)
    assert info.user_id == alice_id
    assert info.username == "alice"
    assert manager.active_count(alice_id) == 1


def test_token_is_not_stored_in_plaintext(manager, alice_id, db_path):
    token = manager.start(alice_id)
    connection = sqlite3.connect(db_path)
    try:
        rows = connection.execute("SELECT * FROM auth_sessions").fetchall()
    finally:
        connection.close()
    assert token not in str(rows)
    assert hash_token(token) in str(rows)


def test_logout_ends_session_and_blocks_reuse(manager, alice_id):
    token = manager.start(alice_id)
    assert manager.end(token) is True
    with pytest.raises(SessionEndedError):
        manager.validate(token)
    assert manager.is_active(token) is False
    assert manager.end(token) is False          # idempotent


def test_unknown_and_empty_tokens_are_rejected(manager):
    for token in ("not-a-real-token", "", None, 123):
        with pytest.raises(SessionNotFoundError):
            manager.validate(token)
    assert manager.end("not-a-real-token") is False
    assert manager.end(None) is False


def test_idle_timeout_ends_session(manager, alice_id, clock):
    token = manager.start(alice_id)
    clock.advance(601)
    with pytest.raises(SessionExpiredError) as caught:
        manager.validate(token)
    assert caught.value.reason == IDLE_TIMEOUT
    clock.advance(-600)                         # time cannot revive it
    assert manager.is_active(token) is False


def test_activity_slides_the_idle_window(manager, alice_id, clock):
    token = manager.start(alice_id)
    for _ in range(4):                          # 4 x 500 s > idle limit
        clock.advance(500)
        manager.validate(token)
    assert manager.is_active(token)


def test_absolute_timeout_applies_even_when_active(manager, alice_id, clock):
    token = manager.start(alice_id)
    with pytest.raises(SessionExpiredError) as caught:
        for _ in range(8):
            clock.advance(500)
            manager.validate(token)
    assert caught.value.reason == "expired"


def test_validate_without_touch_does_not_extend(manager, alice_id, clock):
    token = manager.start(alice_id)
    clock.advance(500)
    manager.validate(token, touch=False)
    clock.advance(200)
    assert manager.is_active(token) is False


def test_end_all_logs_out_every_session(manager, alice_id):
    first, second = manager.start(alice_id), manager.start(alice_id)
    assert manager.end_all(alice_id) == 2
    assert not manager.is_active(first)
    assert not manager.is_active(second)
    assert manager.active_count(alice_id) == 0


def test_sessions_are_independent_per_user(manager, alice_id, db_path):
    DbAuth(db_path=db_path).register("bob", "secret123")
    bob_id = get_user_by_username("bob", db_path=db_path)["id"]
    alice_token, bob_token = manager.start(alice_id), manager.start(bob_id)
    manager.end_all(alice_id)
    assert not manager.is_active(alice_token)
    assert manager.is_active(bob_token)


def test_purge_removes_only_old_finished_sessions(manager, alice_id, clock):
    old, live = manager.start(alice_id), manager.start(alice_id)
    manager.end(old)
    clock.advance(24 * 60 * 60 + 1)
    assert manager.purge() >= 1
    with pytest.raises(SessionNotFoundError):
        manager.validate(old)
    # `live` passed its absolute limit too, so it is purged as well
    assert not manager.is_active(live)


def test_deleting_the_account_removes_its_sessions(manager, alice_id,
                                                   db_path):
    token = manager.start(alice_id)
    connection = sqlite3.connect(db_path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        with connection:
            connection.execute("DELETE FROM users WHERE id = ?",
                               (alice_id,))
    finally:
        connection.close()
    with pytest.raises(SessionNotFoundError):
        manager.validate(token)


# -------------------------------------------------------- GuardedSession
@pytest.fixture()
def guarded(db_path, manager):
    return GuardedSession(db_path=db_path, manager=manager)


def finished_state(score):
    state = GameState(width=10, height=10)
    state.score = score
    return state


def test_guarded_login_and_logout(guarded, alice_id, manager):
    assert not guarded.logged_in
    guarded.login("alice")
    assert guarded.logged_in
    assert guarded.username == "alice"
    token = guarded.token

    guarded.logout()
    assert not guarded.logged_in
    assert guarded.user_id is None and guarded.token is None
    assert not manager.is_active(token)        # server-side end, not just UI


def test_scores_are_not_saved_after_logout(guarded, alice_id, db_path):
    guarded.login("alice")
    guarded.logout()
    assert guarded.save_result(finished_state(50)) is None
    assert get_leaderboard(db_path=db_path) == []


def test_scores_are_saved_while_logged_in(guarded, alice_id, db_path):
    guarded.login("alice")
    assert guarded.finish_game(finished_state(40)) is True
    assert get_leaderboard(db_path=db_path)[0]["score"] == 40


def test_idle_session_stops_counting_as_logged_in(guarded, alice_id, clock,
                                                  db_path):
    guarded.login("alice")
    clock.advance(601)
    assert guarded.logged_in is False
    assert guarded.save_result(finished_state(10)) is None
    assert get_leaderboard(db_path=db_path) == []


def test_touch_keeps_a_long_game_alive(guarded, alice_id, clock):
    guarded.login("alice")
    for _ in range(4):
        clock.advance(500)
        assert guarded.touch() is True
    assert guarded.logged_in


def test_require_login(guarded, alice_id):
    with pytest.raises(NotAuthenticatedError):
        guarded.require_login()
    guarded.login("alice")
    assert guarded.require_login() == alice_id
    guarded.logout()
    with pytest.raises(NotAuthenticatedError):
        guarded.require_login()


def test_logging_in_again_ends_the_previous_session(guarded, alice_id,
                                                    manager):
    guarded.login("alice")
    first = guarded.token
    guarded.login("alice")
    assert guarded.token != first
    assert not manager.is_active(first)


def test_logout_everywhere_ends_other_windows(guarded, alice_id, manager):
    other_window = manager.start(alice_id)
    guarded.login("alice")
    guarded.logout_everywhere()
    assert not guarded.logged_in
    assert not manager.is_active(other_window)


def test_cannot_borrow_another_users_token(guarded, alice_id, db_path,
                                           manager):
    DbAuth(db_path=db_path).register("bob", "secret123")
    bob_id = get_user_by_username("bob", db_path=db_path)["id"]
    guarded.login("alice")
    guarded.token = manager.start(bob_id)       # swap in Bob's token
    assert guarded.logged_in is False
