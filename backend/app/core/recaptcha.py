import httpx
from fastapi import HTTPException

from app.config import settings

def verify_recaptcha(token: str | None) -> None:
    if not settings.recaptcha_enabled:
        return
    if not token:
        raise HTTPException(status_code=400, detail="reCAPTCHA verification required")
    response = httpx.post(
        "https://www.google.com/recaptcha/api/siteverify",
        data={"secret": settings.recaptcha_secret_key, "response": token},
        timeout=5.0,
    )
    if not response.json().get("success"):
        raise HTTPException(status_code=400, detail="reCAPTCHA verification failed")