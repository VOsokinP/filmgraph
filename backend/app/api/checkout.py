from fastapi import APIRouter, Depends, HTTPException, Request

from app.dependencies import get_current_customer_id, get_db
from app.schemas.checkout import ConfirmationOut, PaymentInfo
from app.services import cart_service, checkout_service

router = APIRouter()

@router.post("", response_model = ConfirmationOut)
def checkout(
    payment: PaymentInfo,
    request: Request,
    customer_id: int = Depends(get_current_customer_id),
    conn = Depends(get_db)
):
    cart = request.session.get(cart_service.CART_SESSION_KEY, {})
    if not cart:
        raise HTTPException(status_code=400, detail="Cart is empty")

    if not checkout_service.verify_card(conn, payment.model_dump()):
        raise HTTPException(status_code=402, detail="Payment declined: card details did not match")

    resolved = cart_service.resolve_cart(conn, request.session)
    order_id = checkout_service.place_order(conn, customer_id, resolved)
    cart_service.clear_cart(request.session)

    return {
        "order_id": order_id,
        "items": [
            {
                "movie_id": i["movie_id"],
                "title": i["title"],
                "quantity": i["quantity"],
                "price": i["price"],
            }
            for i in resolved["items"]
        ],
        "total": resolved["total"],
    }
