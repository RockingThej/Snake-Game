"""S2-13: logout and session termination for the Flask API.

Covers TC-AUTH-003 and TC-SEC-005 (a copied cookie must stop working).
"""
import sqlite3

import pytest

from app import create_app

USER = {"username": "alice_1", "email": "alice@example.com",
        "password": "Password1"}
LOGIN = {"username": USER["username"], "password": USER["password"]}


class FakeClock:
    def __init__(self, start=1_000_000.0):
        self.now = start

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


@pytest.fixture()
def clock():
    return FakeClock()


@pytest.fixture()
def flask_app(tmp_path, clock):
    return create_app({
        "TESTING": True,
        "SECRET_KEY": "test",
        "DATABASE": str(tmp_path / "s2.sqlite"),
        "SESSION_CLOCK": clock,
        "SESSION_IDLE_SECONDS": 600,
        "SESSION_ABSOLUTE_SECONDS": 3600,
    })


@pytest.fixture()
def client(flask_app):
    client = flask_app.test_client()
    client.post("/api/auth/register", json=USER)
    return client


def login(client):
    return client.post("/api/auth/login", json=LOGIN)


def test_logout_blocks_protected_endpoints(client):
    login(client)
    assert client.get("/api/auth/me").status_code == 200
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/auth/me").status_code == 401
    res = client.post("/api/scores",
                      json={"food_eaten": 1, "duration_seconds": 1})
    assert res.status_code == 401


def test_copied_cookie_is_useless_after_logout(client, flask_app):
    login(client)
    stolen = client.get_cookie("session").value

    client.post("/api/auth/logout")

    attacker = flask_app.test_client()
    attacker.set_cookie("session", stolen)
    assert attacker.get("/api/auth/me").status_code == 401


def test_logout_when_not_logged_in_is_harmless(client):
    assert client.post("/api/auth/logout").status_code == 200


def test_idle_timeout(client, clock):
    login(client)
    clock.advance(601)
    assert client.get("/api/auth/me").status_code == 401


def test_activity_keeps_the_session_alive(client, clock):
    login(client)
    for _ in range(4):
        clock.advance(500)
        assert client.get("/api/auth/me").status_code == 200


def test_absolute_timeout(client, clock):
    login(client)
    last = 200
    for _ in range(8):
        clock.advance(500)
        last = client.get("/api/auth/me").status_code
    assert last == 401


def test_logout_all_ends_other_sessions(client, flask_app):
    login(client)
    other = flask_app.test_client()
    login(other)

    res = client.post("/api/auth/logout-all")
    assert res.status_code == 200
    assert res.get_json()["sessions_ended"] == 2
    assert other.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me").status_code == 401


def test_logout_all_requires_login(client):
    assert client.post("/api/auth/logout-all").status_code == 401


def test_forged_session_id_is_rejected(client):
    with client.session_transaction() as flask_session:
        flask_session["sid"] = "forged-session-id"
    assert client.get("/api/auth/me").status_code == 401


def test_old_style_user_id_cookie_is_not_trusted(client):
    with client.session_transaction() as flask_session:
        flask_session["user_id"] = 1
    assert client.get("/api/auth/me").status_code == 401


def test_session_token_is_stored_hashed(client, flask_app):
    login(client)
    with client.session_transaction() as flask_session:
        token = flask_session["sid"]
    connection = sqlite3.connect(flask_app.config["DATABASE"])
    try:
        rows = connection.execute("SELECT * FROM sessions").fetchall()
    finally:
        connection.close()
    assert rows and token not in str(rows)


def test_new_login_gets_a_new_session_id(client):
    login(client)
    with client.session_transaction() as flask_session:
        first = flask_session["sid"]
    login(client)
    with client.session_transaction() as flask_session:
        assert flask_session["sid"] != first


def test_api_responses_are_not_cacheable(client):
    login(client)
    res = client.get("/api/auth/me")
    assert res.headers["Cache-Control"] == "no-store"
