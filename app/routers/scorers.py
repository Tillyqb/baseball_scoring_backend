from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/scorers", tags=["scorers"])


@router.post("", response_model=schemas.ScorerOut, status_code=201)
def create_scorer(body: schemas.ScorerCreate, db: Session = Depends(get_db)):
    scorer = models.Scorer(**body.model_dump())
    db.add(scorer)
    db.commit()
    return scorer


@router.get("", response_model=list[schemas.ScorerOut])
def list_scorers(db: Session = Depends(get_db)):
    return db.scalars(
        select(models.Scorer).order_by(models.Scorer.display_name, models.Scorer.id)
    ).all()