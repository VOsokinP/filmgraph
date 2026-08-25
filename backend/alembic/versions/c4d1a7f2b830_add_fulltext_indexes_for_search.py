"""add FULLTEXT indexes on movies.title, movies.director, stars.name

Revision ID: c4d1a7f2b830
Revises: 9a09a3392b92
Create Date: 2026-08-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c4d1a7f2b830'
down_revision: Union[str, Sequence[str], None] = '9a09a3392b92'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE FULLTEXT INDEX ft_movies_title ON movies (title)")
    op.execute("CREATE FULLTEXT INDEX ft_movies_director ON movies (director)")
    op.execute("CREATE FULLTEXT INDEX ft_stars_name ON stars (name)")


def downgrade() -> None:
    op.execute("DROP INDEX ft_stars_name ON stars")
    op.execute("DROP INDEX ft_movies_director ON movies")
    op.execute("DROP INDEX ft_movies_title ON movies")
