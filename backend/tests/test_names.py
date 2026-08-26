import pytest
from sqlalchemy import text

from app.core.names import normalize_name
from app.db.engine import engine
from tests.test_register import clean_customers, register  # noqa: F401


@pytest.mark.parametrize(
    "typed,expected",
    [
        ("john", "John"),
        ("JOHN", "John"),
        ("  john  ", "John"),
        ("mary  jane", "Mary Jane"),
        ("o'brien", "O'Brien"),
        ("jean-luc", "Jean-Luc"),
        ("josé", "José"),
        ("JOSÉ", "José"),
    ],
)
def test_inputs_with_no_case_information_get_title_cased(typed, expected):
    assert normalize_name(typed) == expected


@pytest.mark.parametrize(
    "typed",
    ["McDonald", "DeShawn", "van der Berg", "O'Brien", "MacLeod", "de la Cruz"],
)
def test_deliberate_capitalisation_is_left_alone(typed):
    assert normalize_name(typed) == typed


@pytest.mark.parametrize("typed", ["BrAdY", "FuNkY", "BrAdY FuNkY", "mIxEd"])
def test_random_capitalisation_survives_and_that_is_the_accepted_cost(typed):
    """BrAdY and McDonald have the same shape, so no rule keeps one and flattens the other.
    Preserving deliberate capitalisation was chosen over flattening accidental capitalisation."""
    assert normalize_name(typed) == typed


def test_whitespace_is_collapsed_even_when_case_is_preserved():
    assert normalize_name("  van   der  Berg  ") == "van der Berg"


def test_a_blank_name_normalises_to_empty_rather_than_raising():
    assert normalize_name("   ") == ""


def test_registration_stores_the_normalised_name(client, clean_customers):  # noqa: F811
    body = register(client, firstName="jOHN", lastName="mcdonald").json()  # noqa: F811
    assert body["firstName"] == "jOHN"
    assert body["lastName"] == "Mcdonald"


def test_registration_normalises_a_shouted_name(client, clean_customers):  # noqa: F811
    body = register(client, firstName="JOHN", lastName="SMITH").json()  # noqa: F811
    assert body["firstName"] == "John"
    assert body["lastName"] == "Smith"

    with engine.connect() as conn:
        stored = conn.execute(
            text("SELECT firstName, lastName FROM customers WHERE id = :id"),
            {"id": body["id"]},
        ).mappings().one()
    assert stored["firstName"] == "John"
    assert stored["lastName"] == "Smith"


def test_the_demo_card_carries_the_same_normalised_name(client, clean_customers):  # noqa: F811
    """verify_card matches on the cardholder name, so the card and the customer must agree."""
    body = register(client, firstName="  ada  ", lastName="LOVELACE").json()  # noqa: F811
    card = client.get("/api/cards/me").json()

    assert card["firstName"] == body["firstName"] == "Ada"
    assert card["lastName"] == body["lastName"] == "Lovelace"


def test_a_normalised_name_still_checks_out(client, clean_customers):  # noqa: F811
    register(client, firstName="GRACE", lastName="hopper")  # noqa: F811
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
