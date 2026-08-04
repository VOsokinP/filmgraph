from fastapi import APIRouter, Depends, Request

from app.dependencies import get_db
from app.schemas.cart import CartItemIn, CartOut
from app.services import cart_service

router = APIRouter()

@router.get("", response_model=CartOut)
def get_cart(request: Request, conn=Depends(get_db)) -> CartOut:
    return cart_service.resolve_cart(conn, request.session)

@router.post("/items", response_model=CartOut)
def add_item_to_cart(payload: CartItemIn, request: Request, conn=Depends(get_db)):
    cart_service.add_item(request.session, payload.movie_id, payload.delta)
    return cart_service.resolve_cart(conn, request.session)

@router.delete("/items/{movie_id}", response_model=CartOut)
def delete_from_cart(movie_id: str, request: Request, conn=Depends(get_db)):
    cart_service.remove_item(request.session, movie_id)
    return cart_service.resolve_cart(conn, request.session)