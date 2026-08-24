import os
import pathlib

from sqlalchemy.engine import make_url

BACKEND_DIR = pathlib.Path(__file__).resolve().parents[1]


def _read_dotenv(key: str) -> str | None:
    env_path = BACKEND_DIR / ".env"
    if not env_path.exists():
        return None
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def _resolve_test_url():
    explicit = os.environ.get("TEST_DATABASE_URL")
    if explicit:
        return make_url(explicit)
    source = os.environ.get("DATABASE_URL") or _read_dotenv("DATABASE_URL")
    if not source:
        raise RuntimeError(
            "No database configured for tests. Set TEST_DATABASE_URL, or provide "
            "DATABASE_URL via the environment or backend/.env."
        )
    url = make_url(source)
    if not url.database:
        raise RuntimeError(f"DATABASE_URL has no database name: {source}")
    if url.database.endswith("_test"):
        return url
    return url.set(database=f"{url.database}_test")


TEST_URL = _resolve_test_url()

os.environ["DATABASE_URL"] = TEST_URL.render_as_string(hide_password=False)
os.environ.setdefault("JWT_SECRET_KEY", "test-only-jwt-secret-padded-to-32-bytes-min")
os.environ.setdefault("SESSION_SECRET_KEY", "test-only-session-secret-padded-to-32-bytes")
os.environ["RECAPTCHA_ENABLED"] = "false"

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.db.engine import engine  # noqa: E402
from app.main import app  # noqa: E402

TEST_EMAIL = "fixture.customer@example.com"
TEST_PASSWORD = "fixture-password-123"
UNKNOWN_EMAIL = "nobody.here@example.com"
SEEDED_MOVIE_COUNT = 12


@pytest.fixture(scope="session", autouse=True)
def test_database():
    db_name = TEST_URL.database
    server_url = TEST_URL.set(database=None).render_as_string(hide_password=False)
    admin = create_engine(server_url, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS `{db_name}`"))
        conn.execute(text(f"CREATE DATABASE `{db_name}` CHARACTER SET utf8mb4"))
    admin.dispose()

    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    command.upgrade(cfg, "head")

    _seed()
    yield
    engine.dispose()


def _seed():
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO genres (id, name) VALUES (1, 'Drama'), (2, 'Comedy')")
        )
        conn.execute(
            text(
                "INSERT INTO stars (id, name, birthYear) VALUES "
                "('nm0000001', 'Ada Fixture', 1970), "
                "('nm0000002', 'Grace Sample', 1980)"
            )
        )
        for i in range(1, SEEDED_MOVIE_COUNT + 1):
            movie_id = f"tt{i:07d}"
            conn.execute(
                text(
                    "INSERT INTO movies (id, title, year, director, price) "
                    "VALUES (:id, :title, :year, :director, :price)"
                ),
                {
                    "id": movie_id,
                    "title": f"Fixture Movie {i:02d}",
                    "year": 1990 + i,
                    "director": "Fixture Director",
                    "price": 5.00 + i,
                },
            )
            conn.execute(
                text(
                    "INSERT INTO ratings (movieId, rating, numVotes) "
                    "VALUES (:id, :rating, :votes)"
                ),
                {"id": movie_id, "rating": 9.9 - (i * 0.1), "votes": 1000 + i},
            )
            conn.execute(
                text("INSERT INTO genres_in_movies (genreId, movieId) VALUES (:g, :m)"),
                {"g": 1 if i % 2 else 2, "m": movie_id},
            )
            conn.execute(
                text("INSERT INTO stars_in_movies (starId, movieId) VALUES (:s, :m)"),
                {"s": "nm0000001" if i % 2 else "nm0000002", "m": movie_id},
            )

        conn.execute(
            text(
                "INSERT INTO creditcards (id, firstName, lastName, expiration) "
                "VALUES ('4111111111111111', 'Fixture', 'Customer', '2030-01-01')"
            )
        )
        conn.execute(
            text(
                "INSERT INTO customers (id, firstName, lastName, email, passwordHash, address) "
                "VALUES (1, 'Fixture', 'Customer', :email, :pw, '1 Test Way')"
            ),
            {"email": TEST_EMAIL, "pw": hash_password(TEST_PASSWORD)},
        )


@pytest.fixture()
def db_conn():
    with engine.connect() as conn:
        yield conn


@pytest.fixture()
def clean_orders():
    with engine.begin() as conn:
        orders_mark = conn.execute(text("SELECT COALESCE(MAX(id), 0) FROM orders")).scalar_one()
        sales_mark = conn.execute(text("SELECT COALESCE(MAX(id), 0) FROM sales")).scalar_one()
    yield orders_mark
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM sales WHERE id > :mark"), {"mark": sales_mark})
        conn.execute(text("DELETE FROM orders WHERE id > :mark"), {"mark": orders_mark})


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def auth_client(client):
    response = client.post(
        "/api/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    assert response.status_code == 200, "fixture login failed; seeded customer is wrong"
    return client
