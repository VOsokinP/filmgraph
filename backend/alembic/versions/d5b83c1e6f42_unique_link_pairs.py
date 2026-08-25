"""make stars_in_movies and genres_in_movies pairs unique

Revision ID: d5b83c1e6f42
Revises: c4d1a7f2b830
Create Date: 2026-08-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd5b83c1e6f42'
down_revision: Union[str, Sequence[str], None] = 'c4d1a7f2b830'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

LINK_TABLES = [
    ("stars_in_movies", "starId", "movieId", "uq_stars_in_movies"),
    ("genres_in_movies", "genreId", "movieId", "uq_genres_in_movies"),
]


def upgrade() -> None:
    for table, left, right, index_name in LINK_TABLES:
        op.execute(
            f"ALTER TABLE {table} ADD COLUMN _dedup_id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY"
        )
        op.execute(
            f"""
            DELETE duplicate FROM {table} duplicate
            JOIN {table} keeper
              ON keeper.{left} = duplicate.{left}
             AND keeper.{right} = duplicate.{right}
             AND keeper._dedup_id < duplicate._dedup_id
            """
        )
        op.execute(f"ALTER TABLE {table} DROP COLUMN _dedup_id")
        op.execute(f"ALTER TABLE {table} ADD UNIQUE KEY {index_name} ({left}, {right})")


def downgrade() -> None:
    for table, left, _, index_name in reversed(LINK_TABLES):
        op.execute(f"CREATE INDEX {left} ON {table} ({left})")
        op.execute(f"ALTER TABLE {table} DROP INDEX {index_name}")
