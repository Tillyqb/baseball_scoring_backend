import enum
from datetime import date

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class PlayResult(str, enum.Enum):
    SINGLE = "single"
    DOUBLE = "double"
    TRIPLE = "triple"
    HOME_RUN = "home_run"
    WALK = "walk"
    HIT_BY_PITCH = "hit_by_pitch"
    STRIKEOUT = "strikeout"
    GROUND_OUT = "ground_out"
    FLY_OUT = "fly_out"
    LINE_OUT = "line_out"
    SAC_FLY = "sac_fly"
    SAC_BUNT = "sac_bunt"
    FIELDERS_CHOICE = "fielders_choice"
    DOUBLE_PLAY = "double_play"
    ERROR = "error"


class GameStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    FINAL = "final"


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)

    players: Mapped[list["Player"]] = relationship(back_populates="team")


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), index=True)
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))
    jersey_number: Mapped[int | None] = mapped_column(Integer)

    team: Mapped[Team] = relationship(back_populates="players")


class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(primary_key=True)
    home_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    away_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    game_date: Mapped[date] = mapped_column(Date, default=date.today)
    status: Mapped[GameStatus] = mapped_column(
        Enum(GameStatus, values_callable=lambda e: [m.value for m in e]),
        default=GameStatus.SCHEDULED,
    )
    inning: Mapped[int] = mapped_column(default=1)
    is_top: Mapped[bool] = mapped_column(Boolean, default=True)
    outs: Mapped[int] = mapped_column(default=0)
    home_score: Mapped[int] = mapped_column(default=0)
    away_score: Mapped[int] = mapped_column(default=0)

    plays: Mapped[list["Play"]] = relationship(
        back_populates="game", order_by="Play.id"
    )


class Play(Base):
    """One plate appearance."""

    __tablename__ = "plays"

    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), index=True)
    inning: Mapped[int]
    is_top: Mapped[bool] = mapped_column(Boolean)
    batter_id: Mapped[int] = mapped_column(ForeignKey("players.id"), index=True)
    pitcher_id: Mapped[int | None] = mapped_column(
        ForeignKey("players.id"), index=True
    )
    result: Mapped[PlayResult] = mapped_column(
        Enum(PlayResult, values_callable=lambda e: [m.value for m in e])
    )
    outs_recorded: Mapped[int] = mapped_column(default=0)
    runs_scored: Mapped[int] = mapped_column(default=0)
    rbi: Mapped[int] = mapped_column(default=0)

    game: Mapped[Game] = relationship(back_populates="plays")
