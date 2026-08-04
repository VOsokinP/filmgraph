from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.core.recaptcha import verify_recaptcha
from app.core.security import create_access_token
from app.dependencies import get_current_customer_id, get_db
from app.schemas.auth import CustomerOut, LoginRequest
from app.services import cart_service
from app.services.auth_service import authenticate_customer, get_customer_by_id

router = APIRouter()

@router.post("/login", response_model=CustomerOut)
def login(payload: LoginRequest, response: Response, conn = Depends(get_db)):
    verify_recaptcha(payload.recaptcha_token)
    customer = authenticate_customer(conn, payload.email, payload.password)
    if not customer:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_access_token(customer["id"])
    response.set_cookie(
        key ="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False, # flip to True once served over HTTPS
        max_age=60 * 60 * 24 * 7, # 7 days
        path = "/"
    )
    return customer

@router.post("/logout")
def logout(response: Response, request: Request):
    cart_service.clear_cart(request.session)
    response.delete_cookie(key="access_token", path="/")
    return {"status": "ok"}

@router.get("/me", response_model=CustomerOut)
def me(customer_id: int = Depends(get_current_customer_id), conn = Depends(get_db)):
    customer = get_customer_by_id(conn, customer_id)
    if not customer:
        raise HTTPException(status_code=401, detail="Code: 401 - Not authenticated")
    return customer