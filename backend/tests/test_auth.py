from tests.conftest import TEST_EMAIL, TEST_PASSWORD, UNKNOWN_EMAIL


def test_unknown_email_returns_401_not_500(client):
    response = client.post(
        "/api/auth/login", json={"email": UNKNOWN_EMAIL, "password": "irrelevant"}
    )
    assert response.status_code == 401


def test_wrong_password_returns_401(client):
    response = client.post(
        "/api/auth/login", json={"email": TEST_EMAIL, "password": "not-the-password"}
    )
    assert response.status_code == 401


def test_correct_credentials_return_200_and_set_cookie(client):
    response = client.post(
        "/api/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    assert response.status_code == 200
    assert "access_token" in response.cookies
    assert response.json()["email"] == TEST_EMAIL


def test_failure_messages_are_identical(client):
    unknown = client.post(
        "/api/auth/login", json={"email": UNKNOWN_EMAIL, "password": "irrelevant"}
    )
    wrong = client.post(
        "/api/auth/login", json={"email": TEST_EMAIL, "password": "not-the-password"}
    )
    assert unknown.json() == wrong.json()


def test_password_hash_is_never_returned(client):
    response = client.post(
        "/api/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    assert "passwordHash" not in response.json()


def test_browsing_is_public(client):
    """Browsing must not require a cookie. Gating it put a login wall in front of the demo."""
    assert client.get("/api/movies").status_code == 200
    assert client.get("/api/genres").status_code == 200


def test_cart_is_public_so_an_anonymous_visitor_can_fill_one(client):
    assert client.get("/api/cart").status_code == 200
    assert client.post(
        "/api/cart/items", json={"movie_id": "tt0000001", "delta": 1}
    ).status_code == 200


def test_checkout_still_requires_a_cookie(client):
    assert client.post("/api/checkout", json={}).status_code == 401


def test_browsing_also_works_when_logged_in(auth_client):
    assert auth_client.get("/api/movies").status_code == 200


def test_anonymous_cart_survives_logging_in(client):
    """Fill a cart, then log in at checkout. Losing the cart there would be the worst moment."""
    client.post("/api/cart/items", json={"movie_id": "tt0000001", "delta": 2})
    before = client.get("/api/cart").json()
    assert before["items"][0]["quantity"] == 2

    assert client.post(
        "/api/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    ).status_code == 200

    after = client.get("/api/cart").json()
    assert after["items"] == before["items"]
    assert after["total"] == before["total"]


def test_logout_empties_the_cart(auth_client):
    """A cart left behind at logout would be inherited by the next person on this browser."""
    auth_client.post("/api/cart/items", json={"movie_id": "tt0000001", "delta": 2})
    assert auth_client.get("/api/cart").json()["items"]

    auth_client.post("/api/auth/logout")

    after = auth_client.get("/api/cart").json()
    assert after["items"] == []
    assert after["total"] == 0.0


def test_health_is_open(client):
    assert client.get("/health").status_code == 200
