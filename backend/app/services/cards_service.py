from datetime import date

from sqlalchemy import text
from sqlalchemy.engine import Connection

DEMO_CARD_PREFIX = "4000"
DEMO_CARD_VALID_YEARS = 4


def demo_card_number(customer_id: int) -> str:
    return f"{DEMO_CARD_PREFIX}{customer_id:012d}"


def demo_card_expiration(today: date | None = None) -> date:
    today = today or date.today()
    return date(today.year + DEMO_CARD_VALID_YEARS, today.month, 1)


def create_demo_card(
    conn: Connection, *, customer_id: int, first_name: str, last_name: str
) -> dict:
    card = {
        "id": demo_card_number(customer_id),
        "firstName": first_name,
        "lastName": last_name,
        "expiration": demo_card_expiration(),
        "customerId": customer_id,
    }
    conn.execute(
        text(
            "INSERT INTO creditcards (id, firstName, lastName, expiration, customerId) "
            "VALUES (:id, :firstName, :lastName, :expiration, :customerId)"
        ),
        card,
    )
    return card


def get_card_for_customer(conn: Connection, customer_id: int) -> dict | None:
    row = conn.execute(
        text(
            "SELECT id, firstName, lastName, expiration FROM creditcards "
            "WHERE customerId = :customer_id ORDER BY id LIMIT 1"
        ),
        {"customer_id": customer_id},
    ).mappings().first()
    return dict(row) if row else None
