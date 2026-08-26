from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_customer_id, get_db
from app.schemas.checkout import OrderOut
from app.services import orders_service

router = APIRouter()

@router.get("", response_model=list[OrderOut])
def my_orders(customer_id: int = Depends(get_current_customer_id), conn = Depends(get_db)):
    return orders_service.list_orders(conn, customer_id)

@router.get("/{order_id}", response_model=OrderOut)
def one_order(
    order_id: int,
    customer_id: int = Depends(get_current_customer_id),
    conn = Depends(get_db),
):
    order = orders_service.get_order(conn, order_id, customer_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
