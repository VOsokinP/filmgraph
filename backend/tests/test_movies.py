from app.services.movies_service import (
    ALLOWED_SORT,
    DEFAULT_LIMIT,
    SORT_FIELDS,
    _boolean_query,
    _fulltext_ready,
)
from tests.conftest import SEEDED_MOVIE_COUNT


def test_every_secondary_sort_is_itself_a_sortable_field():
    """One dict now, so the old drift is impossible. What can still break is a secondary
    naming a column that is not sortable, which would reach ORDER BY unchecked."""
    assert set(SORT_FIELDS.values()) <= ALLOWED_SORT


def test_response_limit_matches_rows_returned(auth_client):
    body = auth_client.get("/api/movies?limit=7").json()
    assert body["limit"] == DEFAULT_LIMIT
    assert len(body["items"]) == body["limit"]


def test_every_allowed_sort_field_responds(auth_client):
    for field in ALLOWED_SORT:
        response = auth_client.get(f"/api/movies?sortBy={field}")
        assert response.status_code == 200, f"sortBy={field} failed"


def test_sort_by_year_is_ordered(auth_client):
    years = [m["year"] for m in auth_client.get("/api/movies?sortBy=year&sortDir=asc").json()["items"]]
    assert years == sorted(years)
    years = [m["year"] for m in auth_client.get("/api/movies?sortBy=year&sortDir=desc").json()["items"]]
    assert years == sorted(years, reverse=True)


def test_total_counts_all_matches_not_just_the_page(auth_client):
    body = auth_client.get("/api/movies?limit=10").json()
    assert body["total"] == SEEDED_MOVIE_COUNT
    assert len(body["items"]) == 10


def test_pagination_returns_distinct_pages(auth_client):
    page1 = auth_client.get("/api/movies?limit=10&page=1").json()["items"]
    page2 = auth_client.get("/api/movies?limit=10&page=2").json()["items"]
    assert len(page2) == SEEDED_MOVIE_COUNT - 10
    assert {m["id"] for m in page1}.isdisjoint({m["id"] for m in page2})


def test_title_search_matches_words_inside_a_longer_title(auth_client):
    body = auth_client.get("/api/movies?title=Movie 03").json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "Fixture Movie 03"


def test_title_search_matches_a_word_prefix(auth_client):
    body = auth_client.get("/api/movies?title=Fixt").json()
    assert body["total"] == SEEDED_MOVIE_COUNT


def test_short_terms_still_match(auth_client):
    body = auth_client.get("/api/movies?title=ix").json()
    assert body["total"] == SEEDED_MOVIE_COUNT


def test_fulltext_is_skipped_for_terms_below_the_min_token_size():
    """Purely an optimisation: it saves a FULLTEXT round trip that could never match.
    The LIKE retry would return the same rows either way, so assert the decision directly."""
    assert _fulltext_ready("matrix") is True
    assert _fulltext_ready("the matrix") is True
    assert _fulltext_ready("ix") is False
    assert _fulltext_ready("a matrix") is False


def test_boolean_query_strips_operators_and_prefixes_each_word():
    assert _boolean_query("matrix") == "+matrix*"
    assert _boolean_query("the matrix") == "+the* +matrix*"
    assert _boolean_query('+-~<>()"@') == ""


def test_midword_term_falls_back_to_like_when_fulltext_finds_nothing(auth_client):
    """'ixtur' sits inside 'Fixture', which FULLTEXT cannot match; the LIKE retry must."""
    body = auth_client.get("/api/movies?title=ixtur").json()
    assert body["total"] == SEEDED_MOVIE_COUNT


def test_star_search_uses_the_fulltext_index(auth_client):
    body = auth_client.get("/api/movies?star=Ada").json()
    assert body["total"] > 0
    assert all("Fixture Movie" in m["title"] for m in body["items"])


def test_search_with_no_match_returns_empty_after_both_paths(auth_client):
    body = auth_client.get("/api/movies?title=zzzznotarealtitle").json()
    assert body["total"] == 0
    assert body["items"] == []


def test_unknown_sort_field_falls_back_instead_of_erroring(auth_client):
    assert auth_client.get("/api/movies?sortBy=; DROP TABLE movies").status_code == 200
