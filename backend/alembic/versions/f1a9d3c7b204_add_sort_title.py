"""add a generated sort key so titles order by letter, then number, then symbol

Revision ID: f1a9d3c7b204
Revises: e7c2a4b91d55
Create Date: 2026-08-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f1a9d3c7b204'
down_revision: Union[str, Sequence[str], None] = 'e7c2a4b91d55'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

STRIPPED = "REGEXP_REPLACE(title, '^[^[:alnum:]]+', '')"

SORT_TITLE = f"""
    CONCAT(
        CASE WHEN {STRIPPED} = '' THEN '2'
             WHEN {STRIPPED} REGEXP '^[0-9]' THEN '1'
             ELSE '0' END,
        CASE WHEN {STRIPPED} = '' THEN title ELSE {STRIPPED} END
    )
"""


def upgrade() -> None:
    op.execute(
        f"ALTER TABLE movies ADD COLUMN sort_title VARCHAR(101) "
        f"GENERATED ALWAYS AS ({SORT_TITLE}) STORED"
    )
    op.execute("CREATE INDEX idx_movies_sort_title ON movies (sort_title)")


def downgrade() -> None:
    op.execute("DROP INDEX idx_movies_sort_title ON movies")
    op.execute("ALTER TABLE movies DROP COLUMN sort_title")
