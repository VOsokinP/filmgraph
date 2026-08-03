from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api import auth, movies, stars
from app.config import settings
from app.dependencies import get_current_customer_id

app = FastAPI(title = "FilmGraph API")

app.add_middleware(SessionMiddleware, secret_key=settings.session_secret_key, same_site = "lax")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
_auth_required = [Depends(get_current_customer_id)]
app.include_router(movies.router, prefix="/api/movies", tags=["movies"], dependencies=_auth_required)
app.include_router(stars.router, prefix="/api/stars", tags=["stars"], dependencies=_auth_required)

@app.get("/health")
def health():
    return {"status": "ok"}