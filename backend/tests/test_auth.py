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


def test_protected_route_requires_cookie(client):
    assert client.get("/api/movies").status_code == 401


def test_protected_route_accessible_after_login(auth_client):
    assert auth_client.get("/api/movies").status_code == 200


def test_health_is_open(client):
    assert client.get("/health").status_code == 200
