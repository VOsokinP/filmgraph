from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_db
from app.schemas import StarDetail
from app.services.stars_service import get_star_with_movies

router = APIRouter()

@router.get("/{star_id}", response_model=StarDetail)
def read_star(star_id: str, conn = Depends(get_db)):
    star = get_star_with_movies(conn, star_id)
    if not star:
        raise HTTPException(status_code=404, detail="Star not found")
    return star