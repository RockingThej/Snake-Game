import bcrypt

from app.db import get_db
from tests.conftest import VALID_USER


def test_register_success_hashes_password(app, register):
    res = register()
    assert res.status_code == 201
    assert "password" not in res.get_json()
    with app.app_context():
        row = get_db().execute("SELECT password_hash FROM users").fetchone()
    stored = row["password_hash"]
    assert stored != VALID_USER["password"].encode()
    assert stored.startswith(b"$2")  # bcrypt prefix
    assert bcrypt.checkpw(VALID_USER["password"].encode(), stored)


def test_register_duplicate_username_or_email(register):
    register()
    assert register(email="other@example.com").status_code == 409
    assert register(username="other_user").status_code == 409
    # usernames are case-insensitive
    assert register(username="ALICE_1",
                    email="x@example.com").status_code == 409


def test_register_validation_errors(register):
    assert register(username="a").status_code == 400
    assert register(email="bad").status_code == 400
    assert register(password="weak").status_code == 400


def test_register_without_json_body(client):
    assert client.post("/api/auth/register").status_code == 400


def test_login_logout_flow(client, register):
    register()
    assert client.get("/api/auth/me").status_code == 401

    res = client.post("/api/auth/login",
                      json={"username": "alice_1", "password": "Password1"})
    assert res.status_code == 200
    assert client.get("/api/auth/me").get_json()["username"] == "alice_1"

    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/auth/me").status_code == 401


def test_login_with_email(client, register):
    register()
    res = client.post("/api/auth/login",
                      json={"username": "ALICE@example.com", "password": "Password1"})
    assert res.status_code == 200


def test_login_wrong_password_and_unknown_user_same_message(client, register):
    register()
    wrong = client.post("/api/auth/login",
                        json={"username": "alice_1", "password": "Nope12345"})
    unknown = client.post(
        "/api/auth/login", json={"username": "ghost", "password": "Nope12345"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.get_json() == unknown.get_json()


def test_login_missing_fields(client):
    assert client.post("/api/auth/login", json={}).status_code == 400


def test_session_cookie_flags(client, register):
    register()
    res = client.post("/api/auth/login",
                      json={"username": "alice_1", "password": "Password1"})
    cookie = res.headers["Set-Cookie"]
    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie
