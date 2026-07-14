"""add customers, creditcards, orders, sales tables and movies.price

Revision ID: 9a09a3392b92
Revises: 
Create Date: 2026-07-14 15:55:38.014443

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a09a3392b92'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("firstName", sa.String(50), nullable=False),
        sa.Column("lastName", sa.String(50), nullable=False),
        sa.Column("email", sa.String(50), nullable=False, unique=True),
        sa.Column("passwordHash", sa.String(255), nullable=False),
        sa.Column("address", sa.String(200), nullable=True),
    )

    op.create_table(
        "creditcards",
        sa.Column("id", sa.String(20), primary_key=True),
        sa.Column("firstName", sa.String(50), nullable=False),
        sa.Column("lastName", sa.String(50), nullable=False),
        sa.Column("expiration", sa.Date, nullable=False),
    )

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("customerId", sa.Integer, sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("orderDate", sa.Date, nullable=False),
        sa.Column("total", sa.Numeric(8, 2), nullable=False),
    )

    op.create_table(
        "sales",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("orderId", sa.Integer, sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("movieId", sa.String(10), sa.ForeignKey("movies.id"), nullable=False),
        sa.Column("quantity", sa.Integer, nullable=False),
        sa.Column("price", sa.Numeric(6, 2), nullable=False),
    )

    op.add_column(
        "movies",
        sa.Column("price", sa.Numeric(6, 2), nullable=False, server_default="9.99"),
    )
    op.execute("UPDATE movies SET price = ROUND(RAND() * (29.99-4.99) + 4.99, 2)")

def downgrade() -> None:
    op.drop_column("movies", "price")
    op.drop_table("sales")
    op.drop_table("orders")
    op.drop_table("creditcards")
    op.drop_table("customers")