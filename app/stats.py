from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Play, PlayResult as R
from .schemas import BattingStats, PitchingStats

HITS = {R.SINGLE, R.DOUBLE, R.TRIPLE, R.HOME_RUN}
NOT_AT_BAT = {R.WALK, R.HIT_BY_PITCH, R.SAC_FLY, R.SAC_BUNT}

DEFAULT_OUTS = {
    R.STRIKEOUT: 1,
    R.GROUND_OUT: 1,
    R.FLY_OUT: 1,
    R.LINE_OUT: 1,
    R.SAC_FLY: 1,
    R.SAC_BUNT: 1,
    R.DOUBLE_PLAY: 2,
}


def _ratio(num: float, den: float) -> float:
    return round(num / den, 3) if den else 0.0


def pitching_stats(db: Session, player_id: int) -> PitchingStats:
    plays = db.scalars(select(Play).where(Play.pitcher_id == player_id)).all()
    count = lambda *rs: sum(1 for p in plays if p.result in rs)  # noqa: E731

    outs = sum(p.outs_recorded for p in plays)
    ip = outs / 3
    h, bb, so = count(*HITS), count(R.WALK), count(R.STRIKEOUT)

    return PitchingStats(
        player_id=player_id,
        games=len({p.game_id for p in plays}),
        batters_faced=len(plays),
        outs=outs,
        innings_pitched=f"{outs // 3}.{outs % 3}",
        hits=h,
        runs=sum(p.runs_scored for p in plays),
        home_runs=count(R.HOME_RUN),
        walks=bb,
        hit_by_pitch=count(R.HIT_BY_PITCH),
        strikeouts=so,
        whip=_ratio(h + bb, ip),
        k_per_9=_ratio(so * 9, ip),
        bb_per_9=_ratio(bb * 9, ip),
    )


def batting_stats(db: Session, player_id: int) -> BattingStats:
    plays = db.scalars(select(Play).where(Play.batter_id == player_id)).all()
    count = lambda *rs: sum(1 for p in plays if p.result in rs)  # noqa: E731

    pa = len(plays)
    ab = sum(1 for p in plays if p.result not in NOT_AT_BAT)
    h = sum(1 for p in plays if p.result in HITS)
    d, t, hr = count(R.DOUBLE), count(R.TRIPLE), count(R.HOME_RUN)
    bb, hbp, sf = count(R.WALK), count(R.HIT_BY_PITCH), count(R.SAC_FLY)
    total_bases = h + d + 2 * t + 3 * hr
    avg, slg = _ratio(h, ab), _ratio(total_bases, ab)
    obp = _ratio(h + bb + hbp, ab + bb + hbp + sf)

    return BattingStats(
        player_id=player_id,
        games=len({p.game_id for p in plays}),
        plate_appearances=pa,
        at_bats=ab,
        hits=h,
        doubles=d,
        triples=t,
        home_runs=hr,
        walks=bb,
        hit_by_pitch=hbp,
        strikeouts=count(R.STRIKEOUT),
        sac_flies=sf,
        rbi=sum(p.rbi for p in plays),
        avg=avg,
        obp=obp,
        slg=slg,
        ops=round(obp + slg, 3),
    )
