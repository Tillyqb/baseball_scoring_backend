"""Add scorer profiles and game attribution.

Revision ID: 0002_scorer_attribution
Revises: 0001_baseline
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_scorer_attribution"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scorers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("games") as batch_op:
        batch_op.add_column(sa.Column("scorer_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_games_scorer_id_scorers", "scorers", ["scorer_id"], ["id"]
        )
    op.create_index("ix_games_scorer_id", "games", ["scorer_id"])


def downgrade() -> None:
    op.drop_index("ix_games_scorer_id", table_name="games")
    with op.batch_alter_table("games") as batch_op:
        batch_op.drop_constraint("fk_games_scorer_id_scorers", type_="foreignkey")
        batch_op.drop_column("scorer_id")
    op.drop_table("scorers")