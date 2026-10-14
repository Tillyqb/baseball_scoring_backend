from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..stats import DEFAULT_OUTS, batting_stats, pitching_stats

router = APIRouter(tags=["games"])


def _get_game(db: Session, game_id: int) -> models.Game:
    game = db.get(models.Game, game_id, with_for_update=True)
    if not game:
        raise HTTPException(404, "Game not found")
    return game


@router.post("/games", response_model=schemas.GameOut, status_code=201)
def create_game(body: schemas.GameCreate, db: Session = Depends(get_db)):
    if body.home_team_id == body.away_team_id:
        raise HTTPException(422, "Teams must differ")
    for tid in (body.home_team_id, body.away_team_id):
        if not db.get(models.Team, tid):
            raise HTTPException(404, f"Team {tid} not found")
    data = body.model_dump(exclude_none=True)
    game = models.Game(**data)
    db.add(game)
    db.commit()
    return game


@router.get("/games", response_model=list[schemas.GameOut])
def list_games(db: Session = Depends(get_db)):
    return db.scalars(select(models.Game).order_by(models.Game.id.desc())).all()


@router.get("/games/{game_id}", response_model=schemas.GameOut)
def get_game(game_id: int, db: Session = Depends(get_db)):
    game = db.get(models.Game, game_id)
    if not game:
        raise HTTPException(404, "Game not found")
    return game


@router.post("/games/{game_id}/plays", response_model=schemas.PlayOut, status_code=201)
def record_play(game_id: int, body: schemas.PlayCreate, db: Session = Depends(get_db)):
    game = _get_game(db, game_id)
    if game.status == models.GameStatus.FINAL:
        raise HTTPException(409, "Game is final")

    batter = db.get(models.Player, body.batter_id)
    if not batter:
        raise HTTPException(404, "Batter not found")
    batting_team = game.away_team_id if game.is_top else game.home_team_id
    if batter.team_id != batting_team:
        raise HTTPException(422, "Batter is not on the team currently batting")

    if body.pitcher_id is not None:
        pitcher = db.get(models.Player, body.pitcher_id)
        if not pitcher:
            raise HTTPException(404, "Pitcher not found")
        fielding_team = game.home_team_id if game.is_top else game.away_team_id
        if pitcher.team_id != fielding_team:
            raise HTTPException(422, "Pitcher is not on the team currently fielding")

    outs = (
        body.outs_recorded
        if body.outs_recorded is not None
        else DEFAULT_OUTS.get(body.result, 0)
    )
    if game.outs + outs > 3:
        raise HTTPException(422, "Play would exceed 3 outs")
    rbi = body.rbi if body.rbi is not None else body.runs_scored

    play = models.Play(
        game_id=game.id,
        inning=game.inning,
        is_top=game.is_top,
        batter_id=body.batter_id,
        pitcher_id=body.pitcher_id,
        result=body.result,
        outs_recorded=outs,
        runs_scored=body.runs_scored,
        rbi=rbi,
    )
    db.add(play)

    game.status = models.GameStatus.IN_PROGRESS
    if game.is_top:
        game.away_score += body.runs_scored
    else:
        game.home_score += body.runs_scored
    game.outs += outs
    if game.outs >= 3:
        game.outs = 0
        if game.is_top:
            game.is_top = False
        else:
            game.is_top = True
            game.inning += 1

    db.commit()
    return play


@router.get("/games/{game_id}/plays", response_model=list[schemas.PlayOut])
def list_plays(game_id: int, db: Session = Depends(get_db)):
    return db.scalars(
        select(models.Play).where(models.Play.game_id == game_id).order_by(models.Play.id)
    ).all()


@router.post("/games/{game_id}/final", response_model=schemas.GameOut)
def finalize_game(game_id: int, db: Session = Depends(get_db)):
    game = _get_game(db, game_id)
    game.status = models.GameStatus.FINAL
    db.commit()
    return game


@router.get("/players/{player_id}/stats/batting", response_model=schemas.BattingStats, tags=["stats"])
def player_batting_stats(player_id: int, db: Session = Depends(get_db)):
    if not db.get(models.Player, player_id):
        raise HTTPException(404, "Player not found")
    return batting_stats(db, player_id)


@router.get("/players/{player_id}/stats/pitching", response_model=schemas.PitchingStats, tags=["stats"])
def player_pitching_stats(player_id: int, db: Session = Depends(get_db)):
    if not db.get(models.Player, player_id):
        raise HTTPException(404, "Player not found")
    return pitching_stats(db, player_id)
