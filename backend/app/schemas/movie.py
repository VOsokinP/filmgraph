from pydantic import BaseModel

from app.schemas.genre import GenreRef

class StarRef(BaseModel):
    id: str
    name: str

class MovieBase(BaseModel):
    id: str
    title: str
    year: int
    director: str
    genres: list[GenreRef]
    stars: list[StarRef]
    rating: float | None

class MovieListItem(MovieBase):
    """One row of GET /api/movies — genres/stars truncated to 3 by the query"""

class MovieDetail(MovieBase):
    """GET /api/movies/{id} — genres/stars never truncated."""

class MovieListResponse(BaseModel):
    """The full GET /api/movies response, including pagination info."""
    items: list[MovieListItem]
    total: int
    page: int
    limit: int