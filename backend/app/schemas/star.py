from pydantic import BaseModel

class MovieRef(BaseModel):
    ''' A movie as referenced from star's detail page. id + title only.'''
    id: str
    title: str

class StarDetail(BaseModel):
    ''' A star's detail page.'''
    id: str
    name: str
    birth_year: int | None
    movies: list[MovieRef]