"""Create the legacy baseball scoring schema.

Revision ID: 0001_baseline
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "teams",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "players",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("first_name", sa.String(length=50), nullable=False),
        sa.Column("last_name", sa.String(length=50), nullable=False),
        sa.Column("jersey_number", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_players_team_id", "players", ["team_id"])
    op.create_table(
        "games",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("home_team_id", sa.Integer(), nullable=False),
        sa.Column("away_team_id", sa.Integer(), nullable=False),
        sa.Column("game_date", sa.Date(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("scheduled", "in_progress", "final", name="gamestatus"),
            nullable=False,
        ),
        sa.Column("inning", sa.Integer(), nullable=False),
        sa.Column("is_top", sa.Boolean(), nullable=False),
        sa.Column("outs", sa.Integer(), nullable=False),
        sa.Column("home_score", sa.Integer(), nullable=False),
        sa.Column("away_score", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["away_team_id"], ["teams.id"]),
        sa.ForeignKeyConstraint(["home_team_id"], ["teams.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "plays",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("game_id", sa.Integer(), nullable=False),
        sa.Column("inning", sa.Integer(), nullable=False),
        sa.Column("is_top", sa.Boolean(), nullable=False),
        sa.Column("batter_id", sa.Integer(), nullable=False),
        sa.Column("pitcher_id", sa.Integer(), nullable=True),
        sa.Column(
            "result",
            sa.Enum(
                "single",
                "double",
                "triple",
                "home_run",
                "walk",
                "hit_by_pitch",
                "strikeout",
                "ground_out",
                "fly_out",
                "line_out",
                "sac_fly",
                "sac_bunt",
                "fielders_choice",
                "double_play",
                "error",
                name="playresult",
            ),
            nullable=False,
        ),
        sa.Column("outs_recorded", sa.Integer(), nullable=False),
        sa.Column("runs_scored", sa.Integer(), nullable=False),
        sa.Column("rbi", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["batter_id"], ["players.id"]),
        sa.ForeignKeyConstraint(["game_id"], ["games.id"]),
        sa.ForeignKeyConstraint(["pitcher_id"], ["players.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_plays_batter_id", "plays", ["batter_id"])
    op.create_index("ix_plays_game_id", "plays", ["game_id"])
    op.create_index("ix_plays_pitcher_id", "plays", ["pitcher_id"])


def downgrade() -> None:
    op.drop_index("ix_plays_pitcher_id", table_name="plays")
    op.drop_index("ix_plays_game_id", table_name="plays")
    op.drop_index("ix_plays_batter_id", table_name="plays")
    op.drop_table("plays")
    op.drop_table("games")
    op.drop_index("ix_players_team_id", table_name="players")
    op.drop_table("players")
    op.drop_table("teams")