from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from .models import GameStatus, PlayResult


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TeamCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class TeamOut(ORM, TeamCreate):
    id: int


class PlayerCreate(BaseModel):
    team_id: int
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    jersey_number: int | None = None


class PlayerOut(ORM, PlayerCreate):
    id: int


class ScorerCreate(BaseModel):
    display_name: str = Field(min_length=1, max_length=100)


class ScorerOut(ORM, ScorerCreate):
    id: int


class GameCreate(BaseModel):
    home_team_id: int
    away_team_id: int
    game_date: date | None = None
    scorer_id: int | None = None


class GameOut(ORM):
    id: int
    home_team_id: int
    away_team_id: int
    scorer_id: int | None
    game_date: date
    status: GameStatus
    inning: int
    is_top: bool
    outs: int
    home_score: int
    away_score: int


class PlayCreate(BaseModel):
    batter_id: int
    pitcher_id: int | None = None
    result: PlayResult
    # Defaults to the typical value for the result when omitted.
    outs_recorded: int | None = Field(default=None, ge=0, le=3)
    runs_scored: int = Field(default=0, ge=0, le=4)
    rbi: int | None = Field(default=None, ge=0, le=4)


class PlayOut(ORM):
    id: int
    game_id: int
    inning: int
    is_top: bool
    batter_id: int
    pitcher_id: int | None
    result: PlayResult
    outs_recorded: int
    runs_scored: int
    rbi: int


class PitchingStats(BaseModel):
    player_id: int
    games: int
    batters_faced: int
    outs: int
    innings_pitched: str  # baseball notation, e.g. "6.1"
    hits: int
    runs: int
    home_runs: int
    walks: int
    hit_by_pitch: int
    strikeouts: int
    whip: float
    k_per_9: float
    bb_per_9: float


class BattingStats(BaseModel):
    player_id: int
    games: int
    plate_appearances: int
    at_bats: int
    hits: int
    doubles: int
    triples: int
    home_runs: int
    walks: int
    hit_by_pitch: int
    strikeouts: int
    sac_flies: int
    rbi: int
    avg: float
    obp: float
    slg: float
    ops: float
