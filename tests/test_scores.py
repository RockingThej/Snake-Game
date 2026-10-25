import pytest

from app.scores import ScoreManager
from app.validators import ValidationError


def test_calculate_score_basic():
    assert ScoreManager.calculate_score(5, 0, "easy") == 50
    assert ScoreManager.calculate_score(5, 0, "normal") == 75
    assert ScoreManager.calculate_score(5, 0, "hard") == 100


def test_time_bonus_only_when_food_eaten():
    assert ScoreManager.calculate_score(0, 600, "easy") == 0
    assert ScoreManager.calculate_score(1, 100, "easy") == 10 + 10


def test_calculate_score_rejects_bad_input():
    for args in [(-1, 0, "easy"), (1, -5, "easy"), ("3", 0, "easy"),
                 (1, 1, "nightmare"), (10**9, 0, "easy")]:
        with pytest.raises(ValidationError):
            ScoreManager.calculate_score(*args)


def test_submit_requires_login(client):
    res = client.post(
        "/api/scores", json={"food_eaten": 3, "duration_seconds": 30})
    assert res.status_code == 401


def test_submit_and_fetch_scores(logged_in):
    res = logged_in.post("/api/scores",
                         json={"food_eaten": 4, "duration_seconds": 60, "difficulty": "hard"})
    assert res.status_code == 201
    assert res.get_json()["score"] == int((40 + 6) * 2)

    logged_in.post(
        "/api/scores", json={"food_eaten": 1, "duration_seconds": 5})
    mine = logged_in.get("/api/scores/me").get_json()
    assert mine["best"] == 92
    assert len(mine["scores"]) == 2


def test_client_cannot_send_own_score(logged_in):
    res = logged_in.post("/api/scores",
                         json={"food_eaten": 1, "duration_seconds": 0, "score": 999999})
    assert res.get_json()["score"] == 15  # normal: 10 * 1.5


def test_submit_invalid_payload(logged_in):
    res = logged_in.post(
        "/api/scores", json={"food_eaten": "lots", "duration_seconds": 3})
    assert res.status_code == 400
