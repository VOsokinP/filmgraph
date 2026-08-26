from datetime import date

from sqlalchemy import text

from app.db.engine import engine
from app.services.cards_service import demo_card_expiration, demo_card_number
from tests.conftest import TEST_EMAIL, TEST_PASSWORD
from tests.test_register import NEW, clean_customers, register  # noqa: F401


def test_the_card_number_encodes_nothing_real():
    assert demo_card_number(1) == "4000000000000001"
    assert demo_card_number(973021) == "4000000000973021"
    assert len(demo_card_number(973021)) == 16


def test_the_demo_card_expires_comfortably_in_the_future():
    assert demo_card_expiration(date(2026, 8, 25)) == date(2030, 8, 1)
    assert demo_card_expiration(date(2028, 2, 29)) == date(2032, 2, 1)


def test_registration_creates_a_card_owned_by_the_new_customer(client, clean_customers):  # noqa: F811
    body = register(client).json()  # noqa: F811
    customer_id = body["id"]

    card = client.get("/api/cards/me").json()
    assert card["id"] == demo_card_number(customer_id)
    assert card["firstName"] == NEW["firstName"]
    assert card["lastName"] == NEW["lastName"]

    with engine.connect() as conn:
        owner = conn.execute(
            text("SELECT customerId FROM creditcards WHERE id = :id"), {"id": card["id"]}
        ).scalar_one()
    assert owner == customer_id


def test_the_card_endpoint_requires_a_cookie(client):
    assert client.get("/api/cards/me").status_code == 401


def test_a_customer_with_no_card_gets_404_not_someone_elses(auth_client):
    """The seeded fixture customer predates per-user cards and owns none."""
    assert auth_client.get("/api/cards/me").status_code == 404


def test_two_customers_never_share_a_card(client, clean_customers):  # noqa: F811
    first = register(client, email="one@example.com").json()  # noqa: F811
    client.post("/api/auth/logout")
    second = register(client, email="two@example.com").json()

    assert first["id"] != second["id"]
    assert demo_card_number(first["id"]) != demo_card_number(second["id"])

    card = client.get("/api/cards/me").json()
    assert card["id"] == demo_card_number(second["id"])


def test_the_generated_card_passes_the_real_checkout_check(client, clean_customers):  # noqa: F811
    """verify_card matches number, both names and expiration, so the card we mint must satisfy it."""
    register(client)  # noqa: F811
    card = client.get("/api/cards/me").json()

    client.post("/api/cart/items", json={"movie_id": "tt0000001", "delta": 1})
    response = client.post(
        "/api/checkout",
        json={
            "first_name": card["firstName"],
            "last_name": card["lastName"],
            "card_number": card["id"],
            "expiration": card["expiration"],
        },
    )
    assert response.status_code == 200, response.json()
    assert response.json()["items"][0]["movie_id"] == "tt0000001"


def test_the_seeded_customer_can_still_check_out_with_the_fixture_card(auth_client, clean_orders):
    """Existing accounts predate per-user cards; checkout must not have become card-gated."""
    auth_client.post("/api/cart/items", json={"movie_id": "tt0000002", "delta": 1})
    response = auth_client.post(
        "/api/checkout",
        json={
            "first_name": "Fixture",
            "last_name": "Customer",
            "card_number": "4111111111111111",
            "expiration": "2030-01-01",
        },
    )
    assert response.status_code == 200, response.json()


def test_login_does_not_mint_a_second_card(client, clean_customers):  # noqa: F811
    body = register(client).json()  # noqa: F811
    client.post("/api/auth/logout")
    client.post("/api/auth/login", json={"email": NEW["email"], "password": NEW["password"]})

    with engine.connect() as conn:
        count = conn.execute(
            text("SELECT COUNT(*) FROM creditcards WHERE customerId = :id"), {"id": body["id"]}
        ).scalar_one()
    assert count == 1


def test_the_seeded_fixture_customer_is_unaffected(auth_client):
    assert auth_client.get("/api/auth/me").json()["email"] == TEST_EMAIL
    assert TEST_PASSWORD
