from fastapi import HTTPException, Request

from app.core.security import decode_access_token
from app.db.engine import engine

def get_db():
    with engine.connect() as conn:
        yield conn

def get_current_customer(request: Request) -> int:
    token = request.cookies.get("access_token")
    customer_id = decode_access_token(token) if token else None
    if customer_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return customer_id