# FilmGraph

FilmGraph is a full-stack movie catalog web app: a page listing top-rated movies, a page showing
one movie's full detail, and a page showing one actor's full detail, all cross-linked. It's built
with a FastAPI (Python) JSON API backend, a React + TypeScript frontend, and a MySQL database.

## Database Setup

Targets **MySQL 8.0**.

1. **Get the seed data.** `movie-data.sql` isn't checked into this repo (too large for git).
   Download it from GitHub Releases and place it at `backend/db/movie-data.sql`:
   https://github.com/VOsokinP/filmgraph/releases/download/v1.0-seed-data/movie-data.sql

2. **Create the database and app user:**
   ```sql
   CREATE DATABASE moviedb;
   CREATE USER 'appuser'@'localhost' IDENTIFIED BY 'password';
   GRANT ALL PRIVILEGES ON moviedb.* TO 'appuser'@'localhost';
   ```

3. **Load the schema:**
   ```bash
   mysql -u appuser -p moviedb < backend/db/createtable.sql
   ```

4. **Load the seed data:**
   ```bash
   mysql -u appuser -p moviedb < backend/db/movie-data.sql
   ```

## Backend

Built with **FastAPI** (JSON API), **SQLAlchemy Core** (raw SQL, connection pooling) over
**PyMySQL**, and **pydantic-settings** for config, served by **Uvicorn**.

1. **Install dependencies:**
   ```bash
   cd backend
   pip install -e .
   ```

2. **Configure the database connection.** Copy `.env.example` to `.env` and point it at your
   local MySQL instance from the setup above:
   ```bash
   cp .env.example .env
   ```
   ```
   DATABASE_URL=mysql+pymysql://appuser:password@localhost:3306/moviedb
   ```

Run steps are in **Running Locally** below.

## Frontend

Built with **React + TypeScript** (Vite) as a separate single-page app, using
**react-router-dom** for client-side routing. Three pages — movie list, single movie, single
star — call the FastAPI JSON API and cross-link each other.

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

Run steps are in **Running Locally** below.

## Running Locally

With the database set up (see **Database Setup** above), run both servers in separate terminals.

**Backend** (from `backend/`, after installing dependencies and configuring `.env` per the
**Backend** section above):
```bash
uvicorn app.main:app --reload --port 8000
```
Interactive API docs (auto-generated from the Pydantic schemas) are at
`http://localhost:8000/docs` — useful for exercising each endpoint directly.

**Frontend** (from `frontend/`, after `npm install`):
```bash
npm run dev
```
App runs at `http://localhost:5173` and expects the backend at `http://localhost:8000`; CORS is
already configured in `main.py` for the Vite dev server's origin.

## Deployment

Deployed to a single AWS EC2 instance: `t3.micro`, Ubuntu Server 24.04 LTS (free-tier eligible).
Full step-by-step setup instructions (EC2 launch through Nginx/HTTPS config) are in
[`DEPLOYMENT.md`](./DEPLOYMENT.md) — this section is a quick reference, not a from-scratch guide.

- **`deploy/filmgraph-api.service`** (systemd) — runs the backend as a managed service (Gunicorn
  managing Uvicorn workers), reading `DATABASE_URL` from `backend/.env` on the instance (not
  committed). Restarts automatically on crash or reboot.
- **`deploy/nginx.conf`** — the single public entry point. Serves the built frontend's static files
  from `frontend/dist/`, reverse-proxies `/api/...` to the backend on `127.0.0.1:8000`, and falls
  back to `index.html` for client-side routes so direct links like `/movies/mv1` don't 404.

**Redeploying after a change:**
```bash
ssh -i your-key.pem ubuntu@<elastic-ip>
cd filmgraph
git pull
```
If backend dependencies changed:
```bash
cd backend && source .venv/bin/activate && pip install -e . && cd ..
sudo systemctl restart filmgraph-api
```
If only backend code changed (no new dependencies), the restart alone is enough.

If frontend code changed:
```bash
cd frontend && npm ci && npm run build && cd ..
```
No restart needed — Nginx serves whatever's currently in `dist/` on the next request.

**Live demo:** not running continuously — the instance is spun up on demand rather than left on
between sessions. A free domain and more persistent hosting are planned; until then, available on
request for a live walkthrough.

## Milestones

- [x] `createtable.sql` runs cleanly against a fresh MySQL 8 database
- [x] Data loads without foreign-key errors
- [x] Movie list shows the top 20 movies by rating, correctly sorted, each row with
      title/year/director/3 genres/3 stars/rating
- [x] Every movie title and star name is a working link
- [x] Single movie page shows complete (untruncated) genre and star lists
- [x] Single star page shows name, birth year (or N/A), and every movie, each linked
- [x] Navigation works in both directions between all three page types; "back to list" works from
      any detail page
- [x] README documents database setup, backend run steps, and frontend run steps
- [x] Deployed to a server (e.g. AWS EC2)

## Status

Core read-only flow (movie list / single movie / single star) working end-to-end, deployed to AWS
EC2 behind Nginx and systemd. Instance is run on demand rather than kept up continuously; a domain
is planned for a persistent live link.
