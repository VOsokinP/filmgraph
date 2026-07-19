"""baseline: initial phase 1 schema

Revision ID: 01eeee95977e
Revises:
Create Date: 2026-07-14 17:05:37.757591

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '01eeee95977e'
down_revision: Union[str, Sequence[str], None] =  None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "movies",
        sa.Column("id", sa.String(10), primary_key=True),
        sa.Column("title", sa.String(100), nullable=False),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("director", sa.String(100), nullable=False),
    )

    op.create_table(
        "stars",
        sa.Column("id", sa.String(10), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("birthYear", sa.Integer, nullable=True),
    )

    op.create_table(
        "stars_in_movies",
        sa.Column("starId", sa.String(10), sa.ForeignKey("stars.id"), nullable=False),
        sa.Column("movieId", sa.String(10), sa.ForeignKey("movies.id"), nullable=False),
    )

    op.create_table(
        "genres",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(32), nullable=False),
    )

    op.create_table(
        "genres_in_movies",
        sa.Column("genreId", sa.Integer, sa.ForeignKey("genres.id"), nullable=False),
        sa.Column("movieId", sa.String(10), sa.ForeignKey("movies.id"), nullable=False),
    )

    op.create_table(
        "ratings",
        sa.Column("movieId", sa.String(10), sa.ForeignKey("movies.id"), nullable=False),
        sa.Column("rating", sa.Float, nullable=False),
        sa.Column("numVotes", sa.Integer, nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("ratings")
    op.drop_table("genres_in_movies")
    op.drop_table("genres")
    op.drop_table("stars_in_movies")
    op.drop_table("stars")
    op.drop_table("movies")
