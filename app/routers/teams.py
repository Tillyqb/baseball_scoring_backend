from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(tags=["teams & players"])


@router.post("/teams", response_model=schemas.TeamOut, status_code=201)
def create_team(body: schemas.TeamCreate, db: Session = Depends(get_db)):
    team = models.Team(**body.model_dump())
    db.add(team)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Team name already exists")
    return team


@router.get("/teams", response_model=list[schemas.TeamOut])
def list_teams(db: Session = Depends(get_db)):
    return db.scalars(select(models.Team).order_by(models.Team.name)).all()


@router.post("/players", response_model=schemas.PlayerOut, status_code=201)
def create_player(body: schemas.PlayerCreate, db: Session = Depends(get_db)):
    if not db.get(models.Team, body.team_id):
        raise HTTPException(404, "Team not found")
    player = models.Player(**body.model_dump())
    db.add(player)
    db.commit()
    return player


@router.get("/teams/{team_id}/players", response_model=list[schemas.PlayerOut])
def list_players(team_id: int, db: Session = Depends(get_db)):
    return db.scalars(
        select(models.Player).where(models.Player.team_id == team_id)
    ).all()
