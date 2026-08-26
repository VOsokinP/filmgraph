from datetime import date

from pydantic import BaseModel, field_validator

class PaymentInfo(BaseModel):
    first_name: str
    last_name: str
    card_number: str
    expiration: date

    @field_validator("first_name", "last_name")
    @classmethod
    def strip_whitespace(cls, value: str) -> str:
        return value.strip()

    @field_validator("card_number")
    @classmethod
    def normalize_card_number(cls, value: str) -> str:
        return value.replace(" ", "").replace("-", "")

class CardOut(BaseModel):
    id: str
    firstName: str
    lastName: str
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