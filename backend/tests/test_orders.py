from sqlalchemy import text

from app.db.engine import engine
from tests.test_cards import register  # noqa: F401
from tests.test_register import NEW, clean_customers  # noqa: F401

CARD = {"first_name": "Fixture", "last_name": "Customer", "card_number": "4111111111111111",
        "expiration": "2030-01-01"}


def place_order(client, movie_id="tt0000001", quantity=1, payment=None):
    client.post("/api/cart/items", json={"movie_id": movie_id, "delta": quantity})
    response = client.post("/api/checkout", json=payment or CARD)
    assert response.status_code == 200, response.json()
    return response.json()["order_id"]


def test_orders_require_a_cookie(client):
    assert client.get("/api/orders").status_code == 401
    assert client.get("/api/orders/1").status_code == 401


def test_a_new_account_has_no_orders(auth_client, clean_orders):
    assert auth_client.get("/api/orders").json() == []


def test_an_order_appears_in_the_history_with_its_line_items(auth_client, clean_orders):
    order_id = place_order(auth_client, "tt0000001", 2)

    orders = auth_client.get("/api/orders").json()
    assert len(orders) == 1
    assert orders[0]["id"] == order_id
    assert orders[0]["items"][0]["movie_id"] == "tt0000001"
    assert orders[0]["items"][0]["quantity"] == 2
    assert orders[0]["items"][0]["title"]
    assert orders[0]["total"] > 0


def test_fetching_one_order_returns_the_same_shape(auth_client, clean_orders):
    order_id = place_order(auth_client, "tt0000003", 1)

    listed = auth_client.get("/api/orders").json()[0]
    fetched = auth_client.get(f"/api/orders/{order_id}").json()
    assert fetched == listed


def test_history_is_newest_first(auth_client, clean_orders):
    first = place_order(auth_client, "tt0000004")
    second = place_order(auth_client, "tt0000005")

    ids = [order["id"] for order in auth_client.get("/api/orders").json()]
    assert ids == [second, first]


def test_a_missing_order_is_404(auth_client, clean_orders):
    assert auth_client.get("/api/orders/99999999").status_code == 404


def test_another_customers_order_is_not_visible(client, clean_customers, clean_orders):  # noqa: F811
    """It must 404, not 403: a 403 would confirm the order exists."""
    register(client)  # noqa: F811
    card = client.get("/api/cards/me").json()
    mine = place_order(
        client,
        "tt0000006",
        payment={
            "first_name": card["firstName"],
            "last_name": card["lastName"],
            "card_number": card["id"],
            "expiration": card["expiration"],
        },
    )

    client.post("/api/auth/logout")
    register(client, email="other.person@example.com")

    assert client.get(f"/api/orders/{mine}").status_code == 404
    assert client.get("/api/orders").json() == []


def test_totals_match_what_the_database_stored(auth_client, clean_orders):
    order_id = place_order(auth_client, "tt0000007", 3)

    with engine.connect() as conn:
        stored = conn.execute(
            text("SELECT total FROM orders WHERE id = :id"), {"id": order_id}
        ).scalar_one()

    assert auth_client.get(f"/api/orders/{order_id}").json()["total"] == float(stored)
