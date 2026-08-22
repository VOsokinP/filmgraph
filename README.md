# FilmGraph

[![CI](https://github.com/VOsokinP/FilmGraph/actions/workflows/ci.yml/badge.svg)](https://github.com/VOsokinP/FilmGraph/actions/workflows/ci.yml)

A full-stack movie catalog: browse and search ~9,000 films, drill into a movie or an actor, build a
cart, and check out. Built with a **FastAPI** JSON API, a **React + TypeScript** single-page
frontend, and **MySQL 8**, deployed to AWS EC2 behind Nginx.

## Features

**Authentication** - email + password login, bcrypt-hashed credentials, JWT issued in an httpOnly
cookie and verified on every request. Optional Google reCAPTCHA on the login form. Failed logins
return one generic message for both unknown-email and wrong-password, and the miss path runs a dummy
hash verification so response time doesn't leak which emails are registered.

**Search and browse** - by title, year, director, or star, combined with AND logic and substring
matching (exact for year). Browse by genre or by title's first letter.

**Movie list** - sortable by title, year, rating, or price in either direction, with a stable
secondary sort and prev/next pagination. Page size is clamped server-side to a fixed allowlist, and
the response reports the limit actually applied rather than the one requested.

**Detail pages** - a movie's full genre and cast list, an actor's full filmography sorted by year,
cross-linked in both directions. Per-movie genres and stars are fetched in a fixed number of queries
using `ROW_NUMBER() OVER (PARTITION BY ...)` rather than one query per row.

**Cart and checkout** - cart state lives in a signed session cookie. Checkout verifies the card
against the `creditcards` table and writes a real `orders` row plus one `sales` line item per movie,
in a transaction that rolls back if any insert fails. Payment is mocked; no real processor.

## Tech Stack

| Layer | Choices |
|---|---|
| Backend | FastAPI, Pydantic v2, SQLAlchemy 2.0 Core, PyMySQL, Alembic, PyJWT, passlib/bcrypt |
| Frontend | React 19, TypeScript, Vite, react-router-dom 7, oxlint. No CSS framework or component library - plain CSS driven by custom properties |
| Database | MySQL 8 |
| Tests / CI | pytest against a real MySQL schema, GitHub Actions |
| Deployment | AWS EC2 (Ubuntu), Nginx, systemd, Gunicorn managing Uvicorn workers |


## Getting Started

Requires Python ≥3.11, Node ≥20, and MySQL 8.

### 1. Database

```sql
CREATE DATABASE moviedb CHARACTER SET utf8mb4;
CREATE USER 'appuser'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON moviedb.* TO 'appuser'@'localhost';
```

### 2. Backend

```bash
cd backend
pip install -e .
cp .env.example .env        # then fill in the values below
alembic upgrade head        # the only supported way to build the schema
```

`.env` needs at minimum:

```
DATABASE_URL=mysql+pymysql://appuser:password@localhost:3306/moviedb
JWT_SECRET_KEY=<python -c "import secrets; print(secrets.token_urlsafe(48))">
SESSION_SECRET_KEY=<generate a second, different one>
```

Generate the two secrets separately - they sign different things (identity vs. cart session)

### 3. Seed data

`movie-data.sql` is not in the repo. Download it from
[Releases](https://github.com/VOsokinP/FilmGraph/releases/download/v1.0-seed-data/movie-data.sql),
place it at `backend/db/movie-data.sql`, then:

```bash
mysql -u appuser -p --default-character-set=utf8mb4 moviedb < db/movie-data.sql
```

### 4. Frontend

```bash
cd frontend
npm install
```

### 5. Run

Two terminals:

```bash
cd backend  && uvicorn app.main:app --reload --port 8000   # API + docs at /docs
cd frontend && npm run dev                                  # http://localhost:5173
```

CORS for the Vite dev origin is already configured in `app/main.py`.

## Tests

```bash
cd backend
pip install -e ".[dev]"
pytest -q
```

Tests run against a **real MySQL schema**, not a mock or SQLite - the app leans on MySQL-specific
SQL, so anything else would be testing different code than production runs. `conftest.py` redirects
`DATABASE_URL` to `moviedb_test` before the app's config is imported, drops and rebuilds that
database with `alembic upgrade head`, and seeds a small fixture set. **`moviedb` is never touched.**

One-time grant:

```sql
CREATE DATABASE IF NOT EXISTS moviedb_test CHARACTER SET utf8mb4;
GRANT ALL PRIVILEGES ON moviedb_test.* TO 'appuser'@'localhost';
```

Set `TEST_DATABASE_URL` to point somewhere else (CI does this).

Coverage is deliberately weighted toward the failure modes that actually shipped: unknown email
returning 401 rather than a 500, identical error messages for both login failure paths, the auth
gate on every protected router, page-size clamping matching the reported limit, and an invariant
asserting the sort allowlist and secondary-sort table can't drift apart.

## CI

`.github/workflows/ci.yml` runs on every push and pull request:

- **backend** - boots a `mysql:8` service container, applies migrations, runs pytest
- **frontend** - `npm ci`, oxlint, and a production `vite build`

Both run on Ubuntu from a clean checkout.

## Deployment

One AWS EC2 instance (`t3.micro`, Ubuntu 24.04): Nginx serves the built frontend and reverse-proxies
`/api/...` to Gunicorn/Uvicorn on `127.0.0.1:8000`.
The backend runs under systemd and restarts on crash or reboot.

Full walkthrough in [`DEPLOYMENT.md`](./DEPLOYMENT.md). Redeploy:

```bash
git pull
cd backend  && pip install -e . && sudo systemctl restart filmgraph-api
cd frontend && npm ci && npm run build          # Nginx serves dist/ directly, no restart
```

**Live demo:** the instance runs on demand rather than continuously, so there's no permanent public
link yet. Available on request for a walkthrough.

## Project Layout

```
backend/
  app/
    api/          # routers - HTTP concerns only
    services/     # business logic and all SQL
    schemas/      # Pydantic request/response models
    core/         # security.py, recaptcha.py
    db/           # engine.py - connection management
  alembic/        # migrations - the schema source of truth
  tests/
frontend/src/
  pages/          # one component per route
  components/ui/  # Button, Field, EmptyState, Icons (inline SVG)
  auth/           # AuthContext + AuthProvider + ProtectedRoute
  cart/           # CartCountContext + CartCountProvider
  api/client.ts
deploy/           # systemd unit + nginx config
```

## Roadmap

- [x] Read-only browsing - movie list, movie detail, star detail, cross-linked
- [x] Schema managed entirely by Alembic
- [x] Auth - bcrypt, JWT cookie, gated reCAPTCHA
- [x] Search, browse, sort, pagination
- [x] Cart and transactional checkout
- [x] Deployed to AWS EC2 behind Nginx + systemd
- [x] pytest suite against a real MySQL schema, GitHub Actions CI
- [ ] Error states and retry on failed requests
- [ ] Streaming XML ingestion (lxml) to replace the manual seed load
- [ ] MySQL FULLTEXT search replacing `LIKE` matching
- [ ] Docker
- [ ] HTTPS and a persistent public URL
