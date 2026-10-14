import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.database import get_db
from app.main import app


@pytest.fixture()
def client(engine):
    Session = sessionmaker(bind=engine, autoflush=False)

    def override():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override
    yield TestClient(app)
    app.dependency_overrides.clear()


def setup_game(c):
    home = c.post("/teams", json={"name": "Home"}).json()["id"]
    away = c.post("/teams", json={"name": "Away"}).json()["id"]
    h = c.post("/players", json={"team_id": home, "first_name": "H", "last_name": "P"}).json()["id"]
    a = c.post("/players", json={"team_id": away, "first_name": "A", "last_name": "B"}).json()["id"]
    g = c.post("/games", json={"home_team_id": home, "away_team_id": away}).json()["id"]
    return g, h, a


def test_duplicate_team_conflict(client):
    assert client.post("/teams", json={"name": "X"}).status_code == 201
    assert client.post("/teams", json={"name": "X"}).status_code == 409


def test_scorer_profiles_and_game_attribution(client):
    home = client.post("/teams", json={"name": "Home"}).json()["id"]
    away = client.post("/teams", json={"name": "Away"}).json()["id"]
    scorer = client.post("/scorers", json={"display_name": "Alex Smith"})
    assert scorer.status_code == 201
    scorer_id = scorer.json()["id"]

    game = client.post(
        "/games",
        json={"home_team_id": home, "away_team_id": away, "scorer_id": scorer_id},
    )
    assert game.status_code == 201
    assert game.json()["scorer_id"] == scorer_id
    assert client.get("/scorers").json() == [scorer.json()]

    invalid_game = client.post(
        "/games",
        json={"home_team_id": home, "away_team_id": away, "scorer_id": 999},
    )
    assert invalid_game.status_code == 404


def test_game_validation_and_read_routes(client):
    home = client.post("/teams", json={"name": "Home"}).json()["id"]
    away = client.post("/teams", json={"name": "Away"}).json()["id"]

    assert client.post(
        "/games", json={"home_team_id": home, "away_team_id": home}
    ).status_code == 422
    assert client.post(
        "/games", json={"home_team_id": 999, "away_team_id": away}
    ).status_code == 404

    game = client.post(
        "/games", json={"home_team_id": home, "away_team_id": away}
    ).json()
    assert client.get("/games").json()[0]["id"] == game["id"]
    assert client.get(f"/games/{game['id']}/plays").json() == []
    assert client.get("/games/999").status_code == 404


def test_play_routes_reject_missing_game_batter_and_pitcher(client):
    game_id, _, away_player_id = setup_game(client)

    assert client.post(
        "/games/999/plays", json={"batter_id": away_player_id, "result": "single"}
    ).status_code == 404
    assert client.post(
        f"/games/{game_id}/plays", json={"batter_id": 999, "result": "single"}
    ).status_code == 404
    assert client.post(
        f"/games/{game_id}/plays",
        json={"batter_id": away_player_id, "pitcher_id": 999, "result": "single"},
    ).status_code == 404


def test_bottom_half_score_and_end_of_inning(client):
    game_id, home_player_id, away_player_id = setup_game(client)

    for _ in range(3):
        client.post(
            f"/games/{game_id}/plays",
            json={"batter_id": away_player_id, "pitcher_id": home_player_id, "result": "strikeout"},
        )
    bottom_score = client.post(
        f"/games/{game_id}/plays",
        json={"batter_id": home_player_id, "pitcher_id": away_player_id,
              "result": "single", "runs_scored": 1},
    )
    assert bottom_score.status_code == 201

    for _ in range(3):
        client.post(
            f"/games/{game_id}/plays",
            json={"batter_id": home_player_id, "pitcher_id": away_player_id, "result": "strikeout"},
        )

    game = client.get(f"/games/{game_id}").json()
    assert (game["home_score"], game["inning"], game["is_top"], game["outs"]) == (1, 2, True, 0)


def test_player_stats_reject_unknown_player(client):
    assert client.get("/players/999/stats/batting").status_code == 404
    assert client.get("/players/999/stats/pitching").status_code == 404


def test_team_and_player_lists_and_missing_team(client):
    team_id = client.post("/teams", json={"name": "Visitors"}).json()["id"]
    assert client.get("/teams").json()[0]["id"] == team_id
    assert client.get("/teams/999/players").json() == []
    assert client.post(
        "/players", json={"team_id": 999, "first_name": "No", "last_name": "Team"}
    ).status_code == 404

    player = client.post(
        "/players", json={"team_id": team_id, "first_name": "Sam", "last_name": "Slugger"}
    ).json()
    assert client.get(f"/teams/{team_id}/players").json() == [player]


def test_game_flow_and_half_inning_change(client):
    g, h, a = setup_game(client)
    r = client.post(f"/games/{g}/plays", json={"batter_id": a, "pitcher_id": h, "result": "home_run", "runs_scored": 1})
    assert r.status_code == 201
    for _ in range(3):
        client.post(f"/games/{g}/plays", json={"batter_id": a, "pitcher_id": h, "result": "strikeout"})
    game = client.get(f"/games/{g}").json()
    assert game["away_score"] == 1
    assert (game["inning"], game["is_top"], game["outs"]) == (1, False, 0)
    assert game["status"] == "in_progress"


def test_wrong_team_rejected(client):
    g, h, a = setup_game(client)
    assert client.post(f"/games/{g}/plays", json={"batter_id": h, "result": "single"}).status_code == 422
    assert client.post(f"/games/{g}/plays", json={"batter_id": a, "pitcher_id": a, "result": "single"}).status_code == 422


def test_too_many_outs_rejected(client):
    g, h, a = setup_game(client)
    client.post(f"/games/{g}/plays", json={"batter_id": a, "result": "strikeout"})
    client.post(f"/games/{g}/plays", json={"batter_id": a, "result": "strikeout"})
    r = client.post(f"/games/{g}/plays", json={"batter_id": a, "result": "double_play"})
    assert r.status_code == 422


def test_batting_and_pitching_stats(client):
    g, h, a = setup_game(client)
    for result in ("single", "walk", "strikeout", "home_run"):
        client.post(f"/games/{g}/plays", json={"batter_id": a, "pitcher_id": h, "result": result,
                                               "runs_scored": 1 if result == "home_run" else 0})
    b = client.get(f"/players/{a}/stats/batting").json()
    assert (b["plate_appearances"], b["at_bats"], b["hits"], b["home_runs"], b["rbi"]) == (4, 3, 2, 1, 1)
    assert b["avg"] == 0.667
    assert b["obp"] == 0.75

    p = client.get(f"/players/{h}/stats/pitching").json()
    assert (p["batters_faced"], p["outs"], p["innings_pitched"]) == (4, 1, "0.1")
    assert (p["hits"], p["walks"], p["strikeouts"], p["runs"]) == (2, 1, 1, 1)
    assert p["whip"] == 9.0


def test_final_game_rejects_plays(client):
    g, h, a = setup_game(client)
    client.post(f"/games/{g}/final")
    assert client.post(f"/games/{g}/plays", json={"batter_id": a, "result": "single"}).status_code == 409
