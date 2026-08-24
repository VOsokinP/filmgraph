import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.services import checkout_service

CARD_NUMBER = "4111111111111111"
CARD_HOLDER = {"first_name": "Fixture", "last_name": "Customer"}
EXPIRATION = "2030-01-01"


def payment(card_number: str = CARD_NUMBER, **overrides) -> dict:
    return {**CARD_HOLDER, "card_number": card_number, "expiration": EXPIRATION, **overrides}


def add_to_cart(client, movie_id: str, delta: int = 1):
    response = client.post("/api/cart/items", json={"movie_id": movie_id, "delta": delta})
    assert response.status_code == 200
    return response.json()


def order_row(conn, order_id: int):
    return conn.execute(
        text("SELECT customerId, total FROM orders WHERE id = :id"), {"id": order_id}
    ).mappings().first()


def sale_rows(conn, order_id: int):
    return conn.execute(
        text("SELECT movieId, quantity, price FROM sales WHERE orderId = :id ORDER BY movieId"),
        {"id": order_id},
    ).mappings().all()


def test_checkout_writes_orders_and_sales(auth_client, db_conn, clean_orders):
    add_to_cart(auth_client, "tt0000001", 2)
    add_to_cart(auth_client, "tt0000002", 1)

    response = auth_client.post("/api/checkout", json=payment())
    assert response.status_code == 200
    body = response.json()

    order = order_row(db_conn, body["order_id"])
    assert order is not None
    assert order["customerId"] == 1
    assert float(order["total"]) == pytest.approx(body["total"])

    sales = sale_rows(db_conn, body["order_id"])
    assert [(row["movieId"], row["quantity"]) for row in sales] == [
        ("tt0000001", 2),
        ("tt0000002", 1),
    ]
    assert float(sales[0]["price"]) == pytest.approx(6.00)
    assert float(sales[1]["price"]) == pytest.approx(7.00)

    expected_total = 6.00 * 2 + 7.00 * 1
    assert float(order["total"]) == pytest.approx(expected_total)


def test_checkout_clears_the_cart(auth_client, clean_orders):
    add_to_cart(auth_client, "tt0000003", 1)

    assert auth_client.post("/api/checkout", json=payment()).status_code == 200

    cart = auth_client.get("/api/cart").json()
    assert cart["items"] == []
    assert cart["total"] == 0.0


def test_checkout_rejects_an_empty_cart(auth_client, clean_orders):
    response = auth_client.post("/api/checkout", json=payment())
    assert response.status_code == 400


def test_checkout_declines_a_card_that_does_not_match(auth_client, db_conn, clean_orders):
    add_to_cart(auth_client, "tt0000004", 1)

    response = auth_client.post("/api/checkout", json=payment(last_name="Wrong"))
    assert response.status_code == 402

    written = db_conn.execute(
        text("SELECT COUNT(*) FROM orders WHERE id > :mark"), {"mark": clean_orders}
    ).scalar_one()
    assert written == 0


@pytest.mark.parametrize(
    "card_number",
    ["4111111111111111", "4111 1111 1111 1111", "4111-1111-1111-1111", " 4111111111111111 "],
)
def test_checkout_accepts_spaced_and_dashed_card_numbers(auth_client, clean_orders, card_number):
    add_to_cart(auth_client, "tt0000005", 1)

    response = auth_client.post("/api/checkout", json=payment(card_number))
    assert response.status_code == 200, response.json()


def test_place_order_rolls_back_when_a_line_item_fails(db_conn, clean_orders):
    resolved = {
        "total": 12.00,
        "items": [
            {"movie_id": "tt0000001", "quantity": 1, "price": 6.00},
            {"movie_id": "tt9999999", "quantity": 1, "price": 6.00},
        ],
    }

    with pytest.raises(IntegrityError):
        checkout_service.place_order(db_conn, 1, resolved)

    uncommitted = db_conn.execute(
        text("SELECT COUNT(*) FROM orders WHERE id > :mark"), {"mark": clean_orders}
    ).scalar_one()
    db_conn.rollback()
    assert uncommitted == 0

    with db_conn.engine.connect() as verify:
        committed = verify.execute(
            text("SELECT COUNT(*) FROM orders WHERE id > :mark"), {"mark": clean_orders}
        ).scalar_one()
    assert committed == 0
