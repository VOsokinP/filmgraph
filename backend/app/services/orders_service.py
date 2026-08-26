from sqlalchemy import bindparam, text
from sqlalchemy.engine import Connection


def _items_for_orders(conn: Connection, order_ids: list[int]) -> dict[int, list[dict]]:
    if not order_ids:
        return {}
    rows = conn.execute(
        text(
            """
            SELECT s.orderId, s.movieId, m.title, s.quantity, s.price
            FROM sales s
            JOIN movies m ON m.id = s.movieId
            WHERE s.orderId IN :order_ids
            ORDER BY m.title
            """
        ).bindparams(bindparam("order_ids", expanding=True)),
        {"order_ids": order_ids},
    ).mappings().all()

    items: dict[int, list[dict]] = {}
    for row in rows:
        items.setdefault(row["orderId"], []).append(
            {
                "movie_id": row["movieId"],
                "title": row["title"],
                "quantity": row["quantity"],
                "price": float(row["price"]),
            }
        )
    return items


def list_orders(conn: Connection, customer_id: int) -> list[dict]:
    orders = conn.execute(
        text(
            "SELECT id, orderDate, total FROM orders "
            "WHERE customerId = :customer_id ORDER BY orderDate DESC, id DESC"
        ),
        {"customer_id": customer_id},
    ).mappings().all()

    items = _items_for_orders(conn, [row["id"] for row in orders])
    return [
        {
            "id": row["id"],
            "orderDate": row["orderDate"],
            "total": float(row["total"]),
            "items": items.get(row["id"], []),
        }
        for row in orders
    ]


def get_order(conn: Connection, order_id: int, customer_id: int) -> dict | None:
    """Scoped to the customer, so another customer's order is indistinguishable from one
    that does not exist."""
    row = conn.execute(
        text(
            "SELECT id, orderDate, total FROM orders "
            "WHERE id = :order_id AND customerId = :customer_id"
        ),
        {"order_id": order_id, "customer_id": customer_id},
    ).mappings().first()
    if row is None:
        return None

    return {
        "id": row["id"],
        "orderDate": row["orderDate"],
        "total": float(row["total"]),
        "items": _items_for_orders(conn, [row["id"]]).get(row["id"], []),
    }
