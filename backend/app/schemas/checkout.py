from datetime import date

from pydantic import BaseModel

class PaymentInfo(BaseModel):
    first_name: str
    last_name: str
    card_number: str
    expiration: date

class SaleLine(BaseModel):
    movie_id: str
    title: str
    quantity: int
    price: float

class ConfirmationOut(BaseModel):
    order_id: int
    items: list[SaleLine]
    total: float