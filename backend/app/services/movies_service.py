from sqlalchemy import bindparam, text
from sqlalchemy.engine import Connection

ALLOWED_SORT = {"title", "rating", "price"}
SECONDARY_SORT = {"title": "rating", "rating": "title", "price": "title"}
ALLOWED_LIMITS = {10, 25, 50, 100}

def _genres_for_movies(conn: Connection, movie_ids: list[str], limit_per_movie: int | None) -> dict[str, list[dict]]:
    if not movie_ids:
        return {}
    rank_filter = "WHERE rn <= :limit_per_movie" if limit_per_movie else ""
    query = text(f"""
        SELECT movieId, id, name FROM(
            SELECT gim.movieId, g.id, g.name,
                   ROW_NUMBER() OVER (PARTITION BY gim.movieId ORDER BY g.name) AS rn
            FROM genres_in_movies gim
            JOIN genres g ON gim.genreId = g.id
            WHERE gim.movieId IN :movie_ids
        ) ranked
        {rank_filter}
    """).bindparams(bindparam("movie_ids", expanding=True))

    params = {"movie_ids": movie_ids}
    if limit_per_movie:
        params["limit_per_movie"] = limit_per_movie

    result: dict[str, list[dict]] = {}
    for row in conn.execute(query, params).mappings().all():
        result.setdefault(row["movieId"], []).append({"id": row["id"], "name": row["name"]})
    return result

def _stars_for_movies(conn: Connection, movie_ids: list[str], limit_per_movie: int | None) -> dict[str, list[dict]]:
    if not movie_ids:
        return {}
    rank_filter = "WHERE rn <= :limit_per_movie" if limit_per_movie else ""
    query = text(f"""
        SELECT movieId, id, name FROM (
            SELECT sim.movieId, s.id, s.name,
                ROW_NUMBER() OVER (
                    PARTITION BY sim.movieId
                    ORDER BY star_counts.movie_count DESC, s.name ASC
                ) AS rn
            FROM stars_in_movies sim
            JOIN stars s ON sim.starId = s.id
            JOIN (
                SELECT starId, COUNT(*) AS movie_count
                FROM stars_in_movies
                GROUP BY starId
            ) AS star_counts ON star_counts.starId = s.id
            WHERE sim.movieId IN :movie_ids
        ) ranked
        {rank_filter}
    """).bindparams(bindparam("movie_ids", expanding=True))

    params = {"movie_ids": movie_ids}
    if limit_per_movie:
        params["limit_per_movie"] = limit_per_movie

    result: dict[str, list[dict]] = {}
    for row in conn.execute(query, params).mappings().all():
        result.setdefault(row["movieId"], []).append({"id": row["id"], "name": row["name"]})
    return result
    
def get_movie_by_id(conn: Connection, movie_id: str) -> dict | None:
    movie_row = conn.execute(
        text("SELECT id, title, year, director, price FROM movies WHERE id = :movie_id"),
        {"movie_id": movie_id},
    ).mappings().first()
    if not movie_row:
        return None

    rating_row = conn.execute(
        text("SELECT rating FROM ratings WHERE movieId = :movie_id"),
        {"movie_id": movie_id},
    ).mappings().first()

    return {
        **movie_row,
        "genres": _genres_for_movies(conn, [movie_id], limit_per_movie=None).get(movie_id, []),
        "stars": _stars_for_movies(conn, [movie_id], limit_per_movie=None).get(movie_id, []),
        "rating": rating_row["rating"] if rating_row else None,
    }

def search_movies(
        conn: Connection,
        *,
        title: str | None = None,
        year: int | None = None,
        director: str | None = None,
        star : str | None = None,
        genre_id: int | None = None,
        starts_with: str | None = None,
        sort_by: str = "rating",
        sort_dir: str = "desc",
        page : int = 1,
        limit: int = 20,
) -> tuple[list[dict], int]:
    """ Search/browse/sort/paginate. Calling this with no filters reproduces same behavior 
    as previous implementation "top by rating" list."""
    sort_by = sort_by if sort_by in ALLOWED_SORT else "rating"
    sort_dir = "ASC" if sort_dir.lower() == "asc" else "DESC"
    secondary = SECONDARY_SORT[sort_by]
    limit = limit if limit in ALLOWED_LIMITS else 20
    page = max(page, 1)
    offset = (page - 1) * limit

    where: list[str] = []
    params: dict =  {"limit": limit, "offset": offset}

    if title:
        where.append("m.title LIKE :title")
        params["title"] = f"%{title}%"
    if year is not None:
        where.append("m.year = :year")
        params["year"] = year
    if director:
        where.append("m.director LIKE :director")
        params["director"] = f"%{director}%"
    if star:
        where.append("""
            m.id IN (
                SELECT sim.movieId FROM stars_in_movies sim
                JOIN stars s ON sim.starId = s.id
                WHERE s.name LIKE :star
            )
        """)
        params["star"] = f"%{star}%"
    if genre_id is not None:
        where.append("""
            m.id IN (
                SELECT gim.movieId FROM genres_in_movies gim
                WHERE gim.genreId = :genre_id
            )
        """)
        params["genre_id"] = genre_id
    if starts_with:
        if starts_with == "*":
            where.append("m.title REGEXP '^[^a-zA-Z0-9]'")
        else:
            where.append("m.title LIKE :starts_with")
            params["starts_with"] = f"{starts_with}%"

    where_clause = f"WHERE {' AND '.join(where)}" if where else ""

    # LEFT JOIN and not INNER since an unrated movie should still show up in search/browse results with a null rating
    query = text(f"""
        SELECT m.id, m.title, m.year, m.director, m.price, r.rating,
            COUNT(*) OVER() AS total_count
        FROM movies m
        LEFT JOIN ratings r ON m.id = r.movieId
        {where_clause}
        ORDER BY {sort_by} {sort_dir}, {secondary} {sort_dir}
        LIMIT :limit OFFSET :offset
    """)
    rows = conn.execute(query, params).mappings().all()
    if not rows:
        return [], 0

    total = rows[0]["total_count"]
    movie_ids = [row["id"] for row in rows]
    genres_by_movie = _genres_for_movies(conn, movie_ids, limit_per_movie=3)
    stars_by_movie = _stars_for_movies(conn, movie_ids, limit_per_movie=3)

    movies = [
        {
            "id": r["id"],
            "title": r["title"],
            "year": r["year"],
            "director": r["director"],
            "rating": r["rating"],
            "price": r["price"],
            "genres": genres_by_movie.get(r["id"], []),
            "stars": stars_by_movie.get(r["id"], []),
        }
        for r in rows
    ]
    return movies, total