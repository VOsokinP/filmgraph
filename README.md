# FilmGraph

FilmGraph is a full-stack movie catalog web app: a page listing top-rated movies, a page showing
one movie's full detail, and a page showing one actor's full detail, all cross-linked. It's built
with a FastAPI (Python) JSON API backend, a React + TypeScript frontend, and a MySQL database.

## Database Setup

Targets **MySQL 8.0**.

1. **Get the seed data.** `movie-data.sql` isn't checked into this repo (too large for git).
   Download it from Google Drive and place it at the repo root:
   https://drive.google.com/file/d/1He6C_5d0D1GumfA1Xl2_96uMQoZ2bJ62/view?usp=sharing

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
   mysql -u appuser -p moviedb < movie-data.sql
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

3. **Run the server** (always from `backend/`, never by executing `main.py` directly):
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

Interactive API docs (auto-generated from the Pydantic schemas) are at
`http://localhost:8000/docs` once the server is running — useful for exercising each endpoint
before the frontend exists.

## Status

Work in progress.
