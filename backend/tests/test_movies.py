from app.services.movies_service import ALLOWED_SORT, DEFAULT_LIMIT, SECONDARY_SORT
from tests.conftest import SEEDED_MOVIE_COUNT


def test_sort_tables_cannot_disagree():
    assert ALLOWED_SORT == set(SECONDARY_SORT)


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


def test_title_search_is_substring_matched(auth_client):
    body = auth_client.get("/api/movies?title=Movie 03").json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "Fixture Movie 03"


def test_unknown_sort_field_falls_back_instead_of_erroring(auth_client):
    assert auth_client.get("/api/movies?sortBy=; DROP TABLE movies").status_code == 200
