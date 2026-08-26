# FilmGraph

[![CI](https://github.com/VOsokinP/FilmGraph/actions/workflows/ci.yml/badge.svg)](https://github.com/VOsokinP/FilmGraph/actions/workflows/ci.yml)

A full-stack movie catalog: browse and search ~9,000 films, drill into a movie or an actor, build a
cart, and check out. Built with a **FastAPI** JSON API, a **React + TypeScript** single-page
frontend, and **MySQL 8**, deployed to AWS EC2 behind Nginx.

## Features

**Browsing is public; an account is only needed to check out.** Visitors search, browse and fill a
cart anonymously, and are asked to register or log in at payment. The cart survives that transition,
since it lives in a signed session cookie rather than a table.

**Accounts** - self-serve registration with bcrypt-hashed passwords, and a JWT issued in an httpOnly
cookie and verified on every request. Both auth endpoints are rate limited at the edge and verified
with **reCAPTCHA v3**, which is invisible and score-based, so a visitor never sees a challenge.

The verifier separates two things that are easy to conflate. Google returning *"this is a bot"* is a
verdict and is enforced. Google being unreachable or slow is not a verdict, so the request is allowed
and logged: a demo should not be unreachable because a third party is, and the rate limit is still
standing behind it. Setting the score threshold to `0` runs it in log-only mode, which is how you
watch real scores before enforcing anything. Failed logins return one generic message for both
unknown-email and wrong-password, and the miss path runs a dummy hash verification so response time
doesn't leak which emails are registered. Passwords are capped at 72 **bytes**, the point past which
bcrypt silently ignores input.

**Search** - by title, year, director, or star, combined with AND logic, plus a title box in the
header that works from any page. Browse by genre or by title's first letter.

Title, director and star name are matched with **MySQL FULLTEXT** indexes rather than
`LIKE '%term%'`, which cannot use an index and scanned 60,000 star names on every search. Terms
below `innodb_ft_min_token_size` fall back to `LIKE`, since FULLTEXT cannot index them at all, and a
search that FULLTEXT answers with nothing is retried the same way, which is what keeps a title
starting with a stopword findable.

Median search latency went **73 ms to 4 ms**, of which roughly 9x came from removing a per-request
aggregate over the whole cast table that profiling found was 95% of the request, and 2x from the
FULLTEXT indexes themselves. Method and per-query numbers are recorded outside this repo.

**Movie list** - sortable by title, year, rating, or price in either direction, with a stable
secondary sort and prev/next pagination. Page size is clamped server-side to a fixed allowlist, and
the response reports the limit actually applied rather than the one requested.

**Detail pages** - a movie's full genre and cast list, an actor's full filmography sorted by year,
cross-linked in both directions. Per-movie genres and stars are fetched in a fixed number of queries
using `ROW_NUMBER() OVER (PARTITION BY ...)` rather than one query per row.

**Cart and checkout** - cart state lives in a signed session cookie. Registration issues each
account a demo card, which checkout prefills read-only, so nobody has to invent card details and the
card check stays a real per-user match rather than a formality. Checkout writes a real `orders` row
plus one `sales` line item per movie, in a transaction that rolls back if any insert fails. Payment
is mocked; no real processor.

**Order history** - a profile page listing past orders with their films, each linking back to the
movie. Orders are scoped to their owner, and another customer's order returns 404 rather than 403,
which would confirm it exists.

## Tech Stack

| Layer | Choices |
|---|---|
| Backend | FastAPI, Pydantic v2, SQLAlchemy 2.0 Core, PyMySQL, Alembic, PyJWT, passlib/bcrypt |
| Frontend | React 19, TypeScript, Vite, react-router-dom 7, oxlint. No CSS framework or component library - plain CSS driven by custom properties |
| Database | MySQL 8, with FULLTEXT indexes on title, director and star name |
| Tests / CI | pytest against a real MySQL schema, Vitest + MSW on the frontend, GitHub Actions |
| Containers | Docker multi-stage build, Compose stack for API + MySQL 8 |
| Batch import | lxml streaming parser, CLI loader |
| Deployment | AWS EC2 (Ubuntu), Nginx, systemd, Gunicorn managing Uvicorn workers |


## Getting Started

Two paths. Docker is faster and needs nothing installed but Docker itself; the local install is
what you want if you're going to work on the code.

## Option A - Docker (API + database)

```bash
docker compose up --build
```

Starts MySQL 8 with a persistent volume, waits for its healthcheck, applies `alembic upgrade head`,
and serves the API on <http://localhost:8000> (docs at `/docs`). MySQL is published on **3307** so
it won't collide with a local MySQL on 3306.

`backend/app` is mounted into the container and uvicorn runs with `--reload`, so editing backend
source takes effect immediately. **Changing dependencies or migrations still needs `--build`**,
since those are baked into the image.

Seed data isn't loaded automatically. Download it (step 3 below), then:

```bash
{ echo "SET autocommit=0; SET foreign_key_checks=0; START TRANSACTION;"; \
  cat backend/db/movie-data.sql; \
  echo "COMMIT;"; } | docker compose exec -T db mysql -u appuser -pdevpass moviedb
```

One transaction instead of ~174k autocommits: far faster, and all-or-nothing, so an interrupted
load rolls back rather than leaving a half-populated database.

```bash
docker compose logs -f backend   # follow the API
docker compose down              # stop, keep the data
docker compose down -v           # stop and wipe the database volume
```

The frontend isn't containerized - run it with `npm run dev` (step 4). Compose ships dev-only
default secrets so a clean clone needs no setup; production injects real values through the
environment.

## Option B - Local install

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

The seed data contains **no accounts**: customers and their cards come from registration, so a
freshly seeded database starts empty and the first visitor registers.

A clean exit code doesn't prove every row landed - check one table before trusting the load:

```bash
mysql -u appuser -p moviedb -e "SELECT COUNT(*) FROM movies;"   # expect 9052
```

Full per-table counts are in [`DEPLOYMENT.md`](./DEPLOYMENT.md) step 5.

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

## Loading more data

`backend/etl/` is a batch importer for the [Stanford InfoLab movie
dataset](http://infolab.stanford.edu/pub/movies/), a separate multi-file XML source. It is a local
tool, not part of deployment.

```bash
pip install -e ".[etl]"          # lxml; not installed in production
cd backend/etl/data
curl -O http://infolab.stanford.edu/pub/movies/{mains243.xml,casts124.xml,actors63.xml}
cd ../.. && python -m etl.load etl/data --dry-run    # parse and report, write nothing
python -m etl.load etl/data
```

Streams with `lxml.iterparse` and writes in batches of 1,000, deduplicating against rows already in
the database so a re-run inserts nothing. The source is inconsistent, so every rejected record is
counted and sampled in the run report, and the judgment calls are explicit: cast members missing
from `actors63.xml` become stars with a null birth year rather than being dropped, and Stanford
genre codes map onto the existing names (`Dram` to Drama), unrecognised ones passing through.

## Tests

```bash
cd backend
pip install -e ".[dev,etl]"
pytest -q
```

`lxml` lives in the `etl` extra rather than the runtime dependencies, so production never installs a
parser it does not import. Without it the ETL tests skip cleanly (32 passed, 1 skipped) instead of
failing to import.

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
- **frontend** - `npm ci`, oxlint, Vitest, and a production `vite build`

Both run on Ubuntu from a clean checkout.

## Deployment

One AWS EC2 instance (`t3.micro`, Ubuntu 24.04): Nginx serves the built frontend and reverse-proxies
`/api/...` to Gunicorn/Uvicorn on `127.0.0.1:8000`.
The backend runs under systemd and restarts on crash or reboot.

Full walkthrough and the redeploy runbook are in [`DEPLOYMENT.md`](./DEPLOYMENT.md).

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
  etl/            # batch XML importer (local tool, not deployed)
  tests/
frontend/src/
  pages/          # one component per route
  components/ui/  # Button, Field, EmptyState, Icons (inline SVG)
  auth/           # AuthContext + AuthProvider + ProtectedRoute
  cart/           # CartCountContext + CartCountProvider
  api/client.ts
deploy/           # systemd unit + nginx config
backend/Dockerfile        # multi-stage: build venv, ship runtime only
docker-compose.yml        # local stack - API + MySQL 8
```

## Roadmap

- [x] Read-only browsing - movie list, movie detail, star detail, cross-linked
- [x] Schema managed entirely by Alembic
- [x] Auth - bcrypt, JWT cookie, reCAPTCHA v3, rate-limited login and registration
- [x] Search, browse, sort, pagination
- [x] Cart and transactional checkout
- [x] Public browsing, with login required only at checkout
- [x] Self-serve registration, per-account demo card, order history
- [x] Deployed to AWS EC2 behind Nginx + systemd
- [x] pytest suite against a real MySQL schema, GitHub Actions CI
- [x] Error states and retry on every failed request
- [x] Streaming XML parse feeding batched inserts (lxml), 45k rows/sec
- [x] MySQL FULLTEXT search replacing `LIKE` matching, 73 ms to 4 ms median
- [x] Docker - multi-stage image (334 MB runtime, down from 771 MB) + Compose stack
- [ ] HTTPS and a persistent public URL
