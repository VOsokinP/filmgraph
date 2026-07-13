from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_db
from app.schemas.movie import MovieDetail, MovieListItem
from app.services.movies_service import get_movie_by_id, get_top_movies

router = APIRouter()

@router.get("", response_model=list[MovieListItem])
def list_movies(conn=Depends(get_db)):
    movies = get_top_movies(conn)
    return movies

@router.get("/{movie_id}", response_model=MovieDetail)
def read_movie(movie_id: str, conn=Depends(get_db)):
    movie = get_movie_by_id(conn, movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie