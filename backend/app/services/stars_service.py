from sqlalchemy import text
from sqlalchemy.engine import Connection


def get_star_with_movies(conn: Connection, star_id: str) -> dict | None:
    star_row = conn.execute(
        text("SELECT id, name, birthYear FROM stars WHERE id = :star_id"),
        {"star_id": star_id},
    ).mappings().first()
    if star_row is None:
        return None

    movie_rows = conn.execute(
        text("""
            SELECT m.id AS movie_id, m.title
            FROM stars_in_movies sim
            JOIN movies m ON m.id = sim.movieId
            WHERE sim.starId = :star_id
        """),
        {"star_id": star_id},
    ).mappings().all()

    return {
        "id": star_row["id"],
        "name": star_row["name"],
        "birth_year": star_row["birthYear"],
        "movies": [{"id": r["movie_id"], "title": r["title"]} for r in movie_rows],
    }