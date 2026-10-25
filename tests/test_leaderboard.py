
def _make_player(app, name, foods):
    c = app.test_client()
    c.post("/api/auth/register",
           json={"username": name, "email": f"{name}@example.com", "password": "Password1"})
    c.post("/api/auth/login", json={"username": name, "password": "Password1"})
    for f in foods:
        c.post("/api/scores", json={"food_eaten": f,
               "duration_seconds": 0, "difficulty": "easy"})


def test_empty_leaderboard(client):
    res = client.get("/api/leaderboard")
    assert res.status_code == 200
    assert res.get_json()["leaderboard"] == []


def test_leaderboard_ranks_by_best_score(app, client):
    _make_player(app, "alice", [3, 10])   # best 100
    _make_player(app, "bob", [5])         # best 50
    _make_player(app, "carol", [20, 1])   # best 200
    board = client.get("/api/leaderboard").get_json()["leaderboard"]
    assert [p["username"] for p in board] == ["carol", "alice", "bob"]
    assert [p["rank"] for p in board] == [1, 2, 3]
    assert board[1]["best_score"] == 100
    assert board[1]["games_played"] == 2


def test_leaderboard_limit(app, client):
    for i in range(4):
        _make_player(app, f"player{i}", [i + 1])
    assert len(client.get("/api/leaderboard?limit=2").get_json()
               ["leaderboard"]) == 2


def test_leaderboard_bad_limit(client):
    assert client.get("/api/leaderboard?limit=abc").status_code == 400
    assert client.get("/api/leaderboard?limit=0").status_code == 400
