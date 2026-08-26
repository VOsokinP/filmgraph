import logging

import httpx
from fastapi import HTTPException

from app.config import settings

VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"

logger = logging.getLogger(__name__)


def verify_recaptcha(token: str | None, action: str = "submit") -> None:
    if not settings.recaptcha_enabled:
        return

    if not token:
        raise HTTPException(status_code=400, detail="reCAPTCHA verification required")

    try:
        response = httpx.post(
            VERIFY_URL,
            data={"secret": settings.recaptcha_secret_key, "response": token},
            timeout=settings.recaptcha_timeout_seconds,
        )
        payload = response.json()
    except Exception:
        logger.warning(
            "reCAPTCHA unreachable for action=%s; allowing the request", action, exc_info=True
        )
        return

    if not payload.get("success"):
        logger.info(
            "reCAPTCHA rejected action=%s errors=%s", action, payload.get("error-codes")
        )
        raise HTTPException(status_code=400, detail="reCAPTCHA verification failed")

    returned_action = payload.get("action")
    if returned_action is not None and returned_action != action:
        logger.info(
            "reCAPTCHA action mismatch: token was minted for %s, expected %s",
            returned_action,
            action,
        )
        raise HTTPException(status_code=400, detail="reCAPTCHA verification failed")

    score = payload.get("score")
    if score is None:
        return

    if score < settings.recaptcha_min_score:
        logger.info("reCAPTCHA low score %.2f for action=%s", score, action)
        raise HTTPException(status_code=400, detail="reCAPTCHA verification failed")

    logger.info("reCAPTCHA score %.2f for action=%s", score, action)
