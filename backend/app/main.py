from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import movies, stars

app = FastAPI(title = "FilmGraph API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET"],
)

app.include_router(movies.router, prefix="/api/movies", tags=["movies"])
app.include_router(stars.router, prefix="/api/stars", tags=["stars"])

@app.get("/health")
def health():
    return {"status": "ok"}