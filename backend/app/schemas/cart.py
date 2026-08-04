from pydantic import BaseModel

class CartItemIn(BaseModel):
    movie_id: str
    delta: int = 1

class CartLine(BaseModel):
    movie_id: str
    title: str
    price: float
    quantity: int
    subtotal: float

class CartOut(BaseModel):
    items: list[CartLine]
    total: float