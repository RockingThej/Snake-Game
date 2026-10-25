import pytest

from app import create_app


@pytest.fixture()
def app(tmp_path):
    return create_app({
        "TESTING": True,
        "SECRET_KEY": "test",
        "DATABASE": str(tmp_path / "test.sqlite"),
    })


@pytest.fixture()
def client(app):
    return app.test_client()


VALID_USER = {"username": "alice_1",
              "email": "alice@example.com", "password": "Password1"}


@pytest.fixture()
def register(client):
    def _register(**overrides):
        return client.post("/api/auth/register", json={**VALID_USER, **overrides})
    return _register


@pytest.fixture()
def logged_in(client, register):
    register()
    client.post("/api/auth/login",
                json={"username": VALID_USER["username"], "password": VALID_USER["password"]})
    return client
