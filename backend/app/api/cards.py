from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_customer_id, get_db
from app.schemas.checkout import CardOut
from app.services import cards_service

router = APIRouter()

@router.get("/me", response_model=CardOut)
def my_card(customer_id: int = Depends(get_current_customer_id), conn = Depends(get_db)):
    card = cards_service.get_card_for_customer(conn, customer_id)
    if card is None:
        raise HTTPException(status_code=404, detail="No card on file for this account")
    return card
