from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy import bindparam

def get_movie_by_id(conn: Connection, movie_id: str) -> dict | None:
    movie_row = conn.execute(
        text("SELECT id, title, year, director FROM movies WHERE id = :movie_id"),
        {"movie_id": movie_id},
    ).mappings().first()
    if movie_row is None:
        return None

    genre_rows = conn.execute(
        text("""
            SELECT g.id, g.name
            FROM genres g
            JOIN genres_in_movies gim ON g.id = gim.genreId
            WHERE gim.movieId = :movie_id
             """),
            {"movie_id": movie_id},
    ).mappings().all()

    star_rows = conn.execute(
        text("""
            SELECT s.id, s.name
            FROM stars s
            JOIN stars_in_movies sim ON s.id = sim.starId
            WHERE sim.movieId = :movie_id
            """),
            {"movie_id": movie_id},
    ).mappings().all()

    rating_row = conn.execute(
        text("SELECT rating FROM ratings where movieId = :movie_id"),
        {"movie_id": movie_id},
    ).mappings().first()

    return {
        **movie_row,
        "genres": list(genre_rows),
        "stars": list(star_rows),
        "rating": rating_row["rating"] if rating_row else None,
    }

def get_top_movies(conn: Connection, limit: int = 10) -> list[dict]:
    """ top 20 movies by rating, first 3 genres/stars each """
    top_rows = conn.execute(
        text("""
            SELECT m.id, m.title, m.year, m.director, r.rating
            FROM movies m
            JOIN ratings r ON m.id = r.movieId
            ORDER BY r.rating DESC
            LIMIT :limit
            """),
            {"limit": limit},
    ).mappings().all()
    if not top_rows:
        return []

    movie_ids = [row["id"] for row in top_rows]

    genres_query = text("""
        SELECT movieId, id, name FROM (
            SELECT gim.movieId, g.id, g.name,
                   ROW_NUMBER() OVER (PARTITION BY gim.movieId ORDER BY g.id) AS rn
            FROM genres_in_movies gim
            JOIN genres g ON gim.genreId = g.id
            WHERE gim.movieId IN :movie_ids
        ) ranked
        WHERE rn <= 3
    """).bindparams(bindparam("movie_ids", expanding=True))

    stars_query = text("""
        SELECT movieId, id, name FROM (
            SELECT sim.movieId, s.id, s.name,
                   ROW_NUMBER() OVER (PARTITION BY sim.movieId ORDER BY s.id) AS rn
            FROM stars_in_movies sim
            JOIN stars s ON sim.starId = s.id
            WHERE sim.movieId IN :movie_ids
        ) ranked
        WHERE rn <= 3
    """).bindparams(bindparam("movie_ids", expanding=True))

    genre_rows = conn.execute(genres_query, {"movie_ids": movie_ids}).mappings().all()
    star_rows = conn.execute(stars_query, {"movie_ids": movie_ids}).mappings().all()

    genres_by_movies: dict[str, list[dict]] = {}
    for row in genre_rows:
        genres_by_movies.setdefault(row["movieId"], []).append({"id": row["id"], "name": row["name"]})

    stars_by_movies: dict[str, list[dict]] = {}
    for row in star_rows:
        stars_by_movies.setdefault(row["movieId"], []).append({"id": row["id"], "name": row["name"]})
    
    return [
        {
            "id": m["id"],
            "title": m["title"],
            "year": m["year"],
            "director": m["director"],
            "rating": m["rating"],
            "genres": genres_by_movies.get(m["id"], []),
            "stars": stars_by_movies.get(m["id"], []),
        }
        for m in top_rows
    ]
