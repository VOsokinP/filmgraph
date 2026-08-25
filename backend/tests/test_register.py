import pytest
from sqlalchemy import text

from app.db.engine import engine
from tests.conftest import TEST_EMAIL

NEW = {
    "email": "brand.new@example.com",
    "password": "a-good-enough-password",
    "firstName": "Brand",
    "lastName": "New",
}


@pytest.fixture()
def clean_customers():
    """Remove anything registered during a test, leaving the seeded fixture customer alone."""
    with engine.begin() as conn:
        mark = conn.execute(text("SELECT COALESCE(MAX(id), 0) FROM customers")).scalar_one()
    yield
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM customers WHERE id > :mark"), {"mark": mark})


def register(client, **overrides):
    return client.post("/api/auth/register", json={**NEW, **overrides})


def test_registration_creates_an_account_and_logs_you_in(client, clean_customers):
    response = register(client)
    assert response.status_code == 201

    body = response.json()
    assert body["email"] == NEW["email"]
    assert body["firstName"] == "Brand"
    assert "passwordHash" not in body
    assert "access_token" in response.cookies

    assert client.get("/api/auth/me").json()["email"] == NEW["email"]


def test_the_new_account_can_log_in_afterwards(client, clean_customers):
    assert register(client).status_code == 201
    client.post("/api/auth/logout")

    response = client.post(
        "/api/auth/login", json={"email": NEW["email"], "password": NEW["password"]}
    )
    assert response.status_code == 200


def test_duplicate_email_is_rejected(client, clean_customers):
    assert register(client).status_code == 201
    assert register(client).status_code == 409


def test_an_existing_seeded_email_is_also_rejected(client, clean_customers):
    assert register(client, email=TEST_EMAIL).status_code == 409


@pytest.mark.parametrize(
    "field,value",
    [
        ("password", "short"),
        ("email", "not-an-email"),
        ("firstName", ""),
        ("firstName", "   "),
        ("lastName", ""),
    ],
)
def test_invalid_input_is_rejected(client, clean_customers, field, value):
    response = register(client, **{field: value})
    assert response.status_code == 422

    detail = response.json()["detail"]
    assert isinstance(detail, list)
    assert isinstance(detail[0]["msg"], str)


def test_password_longer_than_bcrypt_can_hash_is_rejected(client, clean_customers):
    """bcrypt silently ignores everything past 72 bytes, so a longer password is a lie."""
    assert register(client, password="x" * 73).status_code == 422


def test_the_byte_limit_is_measured_in_bytes_not_characters(client, clean_customers):
    """25 three-byte characters is 75 bytes, which bcrypt would truncate."""
    assert register(client, password="中" * 25).status_code == 422
    assert register(client, password="中" * 20).status_code == 201


def test_names_are_stripped(client, clean_customers):
    response = register(client, firstName="  Padded  ", lastName="  Name  ")
    assert response.status_code == 201
    assert response.json()["firstName"] == "Padded"
    assert response.json()["lastName"] == "Name"


def test_registering_does_not_disturb_an_anonymous_cart(client, clean_customers):
    client.post("/api/cart/items", json={"movie_id": "tt0000001", "delta": 3})
    before = client.get("/api/cart").json()

    assert register(client).status_code == 201

    assert client.get("/api/cart").json()["items"] == before["items"]
