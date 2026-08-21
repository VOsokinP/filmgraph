from fastapi import APIRouter, Depends, HTTPException, Query
from app.dependencies import get_db
from app.schemas.movie import MovieDetail, MovieListResponse
from app.services.movies_service import DEFAULT_LIMIT, get_movie_by_id, search_movies

router = APIRouter()

@router.get("", response_model=MovieListResponse)
def list_movies(
    title: str | None = None,
    year: int | None = None,
    director: str | None = None,
    star: str | None = None,
    genre_id: int | None = Query(None, alias="genreId"),
    starts_with: str | None = Query(None, alias="startsWith"),
    sort_by: str = Query("rating", alias="sortBy"),
    sort_dir: str = Query("desc", alias="sortDir"),
    page: int = 1,
    limit: int = DEFAULT_LIMIT,
    conn = Depends(get_db),
):
    movies, total, applied_limit = search_movies(
        conn, title=title, year=year, director=director, star=star,
        genre_id=genre_id, starts_with=starts_with,
        sort_by=sort_by, sort_dir=sort_dir, page=page, limit=limit
    )
    return {
        "items": movies,
        "total": total,
        "page": max(page, 1),
        "limit": applied_limit,
    }

@router.get("/{movie_id}", response_model=MovieDetail)
def read_movie(movie_id: str, conn=Depends(get_db)):
    movie = get_movie_by_id(conn, movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie