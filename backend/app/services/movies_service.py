from sqlalchemy import bindparam, text
from sqlalchemy.engine import Connection

SORT_FIELDS = {"title": "rating", "year": "title", "rating": "title", "price": "title"}
ALLOWED_SORT = frozenset(SORT_FIELDS)
LETTER_BUCKET, DIGIT_BUCKET, SYMBOL_BUCKET = "0", "1", "2"
ALLOWED_LIMITS = {10, 25, 50, 100}
DEFAULT_LIMIT = 10
FT_MIN_TOKEN_SIZE = 3


def _fulltext_ready(term: str) -> bool:
    return all(len(word) >= FT_MIN_TOKEN_SIZE for word in term.split())


def _boolean_query(term: str) -> str:
    words = [word.strip('+-~<>()*"@') for word in term.split()]
    return " ".join(f"+{word}*" for word in words if word)

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
                WHERE starId IN (
                    SELECT starId FROM stars_in_movies WHERE movieId IN :movie_ids
                )
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

def _order_column(field: str) -> str:
    """Titles order by the generated key, so leading punctuation is ignored and letters
    sort ahead of digits. Every other field orders by itself."""
    return "sort_title" if field == "title" else field


def _starts_with_prefix(starts_with: str) -> str | None:
    """Translate a browse key into a prefix of sort_title, or None if it is not a valid key.

    Returning a LIKE prefix rather than an expression keeps the index usable.
    """
    if starts_with == "*":
        return f"{SYMBOL_BUCKET}%"
    if len(starts_with) != 1 or not starts_with.isalnum():
        return None
    bucket = DIGIT_BUCKET if starts_with.isdigit() else LETTER_BUCKET
    return f"{bucket}{starts_with}%"


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
        limit: int = DEFAULT_LIMIT,
) -> tuple[list[dict], int, int]:
    """ Search/browse/sort/paginate. Calling this with no filters reproduces same behavior
    as previous implementation "top by rating" list.
    Returns the rows, the total match count, and the limit actually applied."""
    sort_by = sort_by if sort_by in ALLOWED_SORT else "rating"
    sort_dir = "ASC" if sort_dir.lower() == "asc" else "DESC"
    primary = _order_column(sort_by)
    secondary = _order_column(SORT_FIELDS[sort_by])
    limit = limit if limit in ALLOWED_LIMITS else DEFAULT_LIMIT
    page = max(page, 1)
    offset = (page - 1) * limit

    def build_filters(use_fulltext: bool) -> tuple[list[str], list[str], dict]:
        joins: list[str] = []
        where: list[str] = []
        params: dict = {"limit": limit, "offset": offset}

        def match_clause(field: str, term: str, column: str) -> str:
            if use_fulltext and _fulltext_ready(term):
                params[field] = _boolean_query(term)
                return f"MATCH({column}) AGAINST (:{field} IN BOOLEAN MODE)"
            params[field] = f"%{term}%"
            return f"{column} LIKE :{field}"

        def text_filter(field: str, term: str, column: str) -> None:
            where.append(match_clause(field, term, column))

        if title:
            text_filter("title", title, "m.title")
        if year is not None:
            where.append("m.year = :year")
            params["year"] = year
        if director:
            text_filter("director", director, "m.director")
        if star:
            # Joined, not `m.id IN (...)`: with a FULLTEXT predicate the optimiser loses the
            # row estimate for the subquery and falls back to scanning movies once per match.
            joins.append(f"""
                JOIN (
                    SELECT DISTINCT sim.movieId
                    FROM stars_in_movies sim
                    JOIN stars s ON sim.starId = s.id
                    WHERE {match_clause("star", star, "s.name")}
                ) star_match ON star_match.movieId = m.id
            """)
        if genre_id is not None:
            where.append("""
                m.id IN (
                    SELECT gim.movieId FROM genres_in_movies gim
                    WHERE gim.genreId = :genre_id
                )
            """)
            params["genre_id"] = genre_id
        if starts_with:
            prefix = _starts_with_prefix(starts_with)
            if prefix is not None:
                where.append("m.sort_title LIKE :starts_with")
                params["starts_with"] = prefix

        return joins, where, params

    # LEFT JOIN and not INNER since an unrated movie should still show up in search/browse results with a null rating
    def run(use_fulltext: bool):
        joins, where, params = build_filters(use_fulltext)
        where_clause = f"WHERE {' AND '.join(where)}" if where else ""
        query = text(f"""
            SELECT m.id, m.title, m.year, m.director, m.price, r.rating,
                COUNT(*) OVER() AS total_count
            FROM movies m
            LEFT JOIN ratings r ON m.id = r.movieId
            {' '.join(joins)}
            {where_clause}
            ORDER BY {primary} {sort_dir}, {secondary} {sort_dir}
            LIMIT :limit OFFSET :offset
        """)
        return conn.execute(query, params).mappings().all()

    searched_text = any(term for term in (title, director, star))
    rows = run(use_fulltext=True)
    if not rows and searched_text:
        rows = run(use_fulltext=False)
    if not rows:
        return [], 0, limit

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
    return movies, total, limit