from pydantic import BaseModel

class GenreRef(BaseModel):
    id: int
    name: str