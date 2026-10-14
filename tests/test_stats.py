import pytest

from app import models
from app.models import PlayResult as R
from app.stats import DEFAULT_OUTS, _ratio, batting_stats, pitching_stats


@pytest.fixture()
def db(engine):
    from sqlalchemy.orm import sessionmaker

    session = sessionmaker(bind=engine)()
    away = models.Team(name="Away")
    home = models.Team(name="Home")
    session.add_all([away, home])
    session.flush()
    batter = models.Player(team_id=away.id, first_name="A", last_name="B")
    pitcher = models.Player(team_id=home.id, first_name="H", last_name="P")
    game = models.Game(home_team_id=home.id, away_team_id=away.id)
    session.add_all([batter, pitcher, game])
    session.commit()
    session.info.update(batter=batter.id, pitcher=pitcher.id, game=game.id)
    yield session
    session.close()


def add_play(db, result, outs=0, runs=0, rbi=0, pitcher=True):
    db.add(
        models.Play(
            game_id=db.info["game"],
            inning=1,
            is_top=True,
            batter_id=db.info["batter"],
            pitcher_id=db.info["pitcher"] if pitcher else None,
            result=result,
            outs_recorded=outs,
            runs_scored=runs,
            rbi=rbi,
        )
    )
    db.commit()


def test_ratio_handles_zero_denominator():
    assert _ratio(1, 0) == 0.0
    assert _ratio(1, 3) == 0.333


def test_default_outs():
    assert DEFAULT_OUTS[R.DOUBLE_PLAY] == 2
    assert DEFAULT_OUTS[R.STRIKEOUT] == 1
    assert R.SINGLE not in DEFAULT_OUTS
    assert R.WALK not in DEFAULT_OUTS


def test_batting_no_plays_is_all_zero(db):
    s = batting_stats(db, db.info["batter"])
    assert (s.plate_appearances, s.at_bats, s.avg, s.obp, s.slg, s.ops) == (0, 0, 0, 0, 0, 0)


def test_batting_excludes_walks_hbp_and_sacrifices_from_at_bats(db):
    for r in (R.WALK, R.HIT_BY_PITCH, R.SAC_FLY, R.SAC_BUNT, R.SINGLE):
        add_play(db, r)
    s = batting_stats(db, db.info["batter"])
    assert (s.plate_appearances, s.at_bats, s.hits) == (5, 1, 1)
    assert s.avg == 1.0
    assert s.obp == 0.75  # (1 + 1 + 1) / (1 + 1 + 1 + 1)


def test_batting_slugging_and_ops(db):
    for r in (R.SINGLE, R.DOUBLE, R.TRIPLE, R.HOME_RUN):
        add_play(db, r)
    s = batting_stats(db, db.info["batter"])
    assert s.slg == 2.5  # 10 total bases / 4 AB
    assert s.ops == 3.5


def test_batting_sums_rbi_and_counts_games(db):
    add_play(db, R.SINGLE, rbi=2)
    add_play(db, R.HOME_RUN, runs=1, rbi=3)
    s = batting_stats(db, db.info["batter"])
    assert s.rbi == 5
    assert s.games == 1


def test_pitching_no_plays_is_all_zero(db):
    s = pitching_stats(db, db.info["pitcher"])
    assert (s.batters_faced, s.outs, s.innings_pitched, s.whip) == (0, 0, "0.0", 0)


@pytest.mark.parametrize("outs,expected", [(1, "0.1"), (3, "1.0"), (7, "2.1"), (8, "2.2")])
def test_pitching_innings_notation(db, outs, expected):
    for _ in range(outs):
        add_play(db, R.STRIKEOUT, outs=1)
    assert pitching_stats(db, db.info["pitcher"]).innings_pitched == expected


def test_pitching_rates(db):
    for _ in range(3):
        add_play(db, R.STRIKEOUT, outs=1)
    add_play(db, R.SINGLE, runs=1)
    add_play(db, R.WALK)
    s = pitching_stats(db, db.info["pitcher"])
    assert (s.hits, s.walks, s.strikeouts, s.runs) == (1, 1, 3, 1)
    assert s.whip == 2.0
    assert s.k_per_9 == 27.0
    assert s.bb_per_9 == 9.0


def test_pitching_ignores_plays_without_pitcher(db):
    add_play(db, R.SINGLE, pitcher=False)
    assert pitching_stats(db, db.info["pitcher"]).batters_faced == 0
