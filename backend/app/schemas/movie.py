from pydantic import BaseModel

class GenreRef(BaseModel):
    id: int
    name: str

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
    """GET /api/movies — genres/stars pre-truncated to 3 by the query."""

class MovieDetail(MovieBase):
    """GET /api/movies/{id} — genres/stars never truncated."""