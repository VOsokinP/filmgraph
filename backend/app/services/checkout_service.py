from datetime import date

from sqlalchemy import text
from sqlalchemy.engine import Connection

def verify_card(conn: Connection, payment: dict) -> bool:
    row = conn.execute(
        text("""
                SELECT id FROM creditcards
                WHERE id = :card_number AND firstName = :first_name
                AND lastName = :last_name AND expiration = :expiration
            """),
            payment,
    ).first()
    return row is not None

def place_order(conn: Connection, customer_id: int, resolved_card: dict) -> int:
    try:
        order_result = conn.execute(
            text("INSERT INTO orders (customerId, orderDate, total) VALUES (:customer_id, :order_date, :total)"),
            { "customer_id": customer_id, "order_date": date.today(), "total": resolved_card["total"] },
        )
        order_id = order_result.lastrowid

        for item in resolved_card["items"]:
            conn.execute(
                text("""
                    INSERT INTO sales (orderId, movieId, quantity, price)
                    VALUES (:order_id, :movie_id, :quantity, :price)
                """),
                {
                    "order_id": order_id,
                    "movie_id": item["movie_id"],
                    "quantity": item["quantity"],
                    "price": item["price"],
                },
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return order_id