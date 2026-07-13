from sqlalchemy import text
from sqlalchemy.engine import Connection

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