import pytest
from sqlalchemy import text

from app.db.engine import engine

TRICKY = [
    ("zz000001", "Alpha"),
    ("zz000002", "-30-"),
    ("zz000003", "300"),
    ("zz000004", ".com Story"),
    ("zz000005", "zeta"),
]
TITLES = {title for _, title in TRICKY}


@pytest.fixture()
def tricky_titles():
    with engine.begin() as conn:
        for movie_id, title in TRICKY:
            conn.execute(
                text(
                    "INSERT INTO movies (id, title, year, director, price) "
                    "VALUES (:id, :title, 2000, 'Sort Fixture', 9.99)"
                ),
                {"id": movie_id, "title": title},
            )
    yield
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM movies WHERE id LIKE 'zz%'"),
        )


def titles_in_order(client, direction="asc"):
    body = client.get(f"/api/movies?sortBy=title&sortDir={direction}&limit=100").json()
    return [m["title"] for m in body["items"] if m["title"] in TITLES]


def test_letters_sort_before_digits(auth_client, tricky_titles):
    ordered = titles_in_order(auth_client)
    letters = [t for t in ordered if t in {"Alpha", ".com Story", "zeta"}]
    digits = [t for t in ordered if t in {"-30-", "300"}]
    assert ordered == letters + digits


def test_leading_punctuation_is_ignored_when_sorting(auth_client, tricky_titles):
    """'.com Story' sorts under C, between Alpha and zeta, not ahead of everything."""
    ordered = titles_in_order(auth_client)
    assert ordered[:3] == ["Alpha", ".com Story", "zeta"]


def test_full_expected_order(auth_client, tricky_titles):
    assert titles_in_order(auth_client) == ["Alpha", ".com Story", "zeta", "-30-", "300"]


def test_descending_is_the_exact_reverse(auth_client, tricky_titles):
    assert titles_in_order(auth_client, "desc") == list(
        reversed(titles_in_order(auth_client, "asc"))
    )


def test_browse_by_letter_ignores_leading_punctuation(auth_client, tricky_titles):
    """'.com Story' must be reachable under C, which it was not before sort_title existed."""
    body = auth_client.get("/api/movies?startsWith=C&limit=100").json()
    assert ".com Story" in [m["title"] for m in body["items"]]


def test_browse_by_digit_ignores_leading_punctuation(auth_client, tricky_titles):
    body = auth_client.get("/api/movies?startsWith=3&limit=100").json()
    found = [m["title"] for m in body["items"]]
    assert "-30-" in found
    assert "300" in found


def test_an_invalid_browse_key_is_ignored_rather_than_filtering(auth_client, tricky_titles):
    """A multi-character or LIKE-wildcard key must not reach the query."""
    everything = auth_client.get("/api/movies?limit=10").json()["total"]
    for key in ["%", "_", "ab", "'"]:
        assert auth_client.get(f"/api/movies?startsWith={key}&limit=10").json()["total"] == everything
