from fastapi import APIRouter, Depends

from app.dependencies import get_db
from app.schemas.genre import GenreRef
from app.services.genres_service import list_genres

router = APIRouter()

@router.get("", response_model=list[GenreRef])
def get_genres(conn = Depends(get_db)):
    return list_genres(conn)