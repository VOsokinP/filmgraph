"""link creditcards to the customer who owns them

Revision ID: e7c2a4b91d55
Revises: d5b83c1e6f42
Create Date: 2026-08-25 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'e7c2a4b91d55'
down_revision: Union[str, Sequence[str], None] = 'd5b83c1e6f42'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("creditcards", sa.Column("customerId", sa.Integer, nullable=True))
    op.create_index("ix_creditcards_customerId", "creditcards", ["customerId"])
    op.create_foreign_key(
        "fk_creditcards_customer", "creditcards", "customers", ["customerId"], ["id"]
    )


def downgrade() -> None:
    op.drop_constraint("fk_creditcards_customer", "creditcards", type_="foreignkey")
    op.drop_index("ix_creditcards_customerId", table_name="creditcards")
    op.drop_column("creditcards", "customerId")
