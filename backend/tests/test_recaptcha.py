"""The verifier had never run anywhere, so every branch is asserted here rather than trusted.

The distinction that matters: a transport failure is not a verdict. Google being unreachable must
not lock people out of the site; Google saying "this is a bot" must.
"""
import httpx
import pytest
from fastapi import HTTPException

from app.core import recaptcha
from app.core.recaptcha import verify_recaptcha


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


@pytest.fixture()
def enabled(monkeypatch):
    monkeypatch.setattr(recaptcha.settings, "recaptcha_enabled", True)
    monkeypatch.setattr(recaptcha.settings, "recaptcha_secret_key", "test-secret")
    monkeypatch.setattr(recaptcha.settings, "recaptcha_min_score", 0.5)


def respond_with(monkeypatch, payload):
    calls = []

    def fake_post(url, **kwargs):
        calls.append((url, kwargs))
        return FakeResponse(payload)

    monkeypatch.setattr(recaptcha.httpx, "post", fake_post)
    return calls


def raise_with(monkeypatch, error):
    def fake_post(url, **kwargs):
        raise error

    monkeypatch.setattr(recaptcha.httpx, "post", fake_post)


def test_disabled_never_calls_google(monkeypatch):
    monkeypatch.setattr(recaptcha.settings, "recaptcha_enabled", False)
    calls = respond_with(monkeypatch, {"success": False})

    verify_recaptcha(None)

    assert calls == []


def test_a_missing_token_is_rejected(enabled, monkeypatch):
    calls = respond_with(monkeypatch, {"success": True, "score": 0.9})

    with pytest.raises(HTTPException) as raised:
        verify_recaptcha(None)

    assert raised.value.status_code == 400
    assert calls == [], "no point asking Google about a token we never received"


def test_a_good_score_passes(enabled, monkeypatch):
    respond_with(monkeypatch, {"success": True, "score": 0.9})
    verify_recaptcha("token")


def test_a_low_score_is_rejected(enabled, monkeypatch):
    respond_with(monkeypatch, {"success": True, "score": 0.1})

    with pytest.raises(HTTPException) as raised:
        verify_recaptcha("token")
    assert raised.value.status_code == 400


def test_the_threshold_boundary_is_inclusive(enabled, monkeypatch):
    respond_with(monkeypatch, {"success": True, "score": 0.5})
    verify_recaptcha("token")


def test_a_zero_threshold_accepts_anything_which_is_log_only_mode(enabled, monkeypatch):
    monkeypatch.setattr(recaptcha.settings, "recaptcha_min_score", 0.0)
    respond_with(monkeypatch, {"success": True, "score": 0.0})
    verify_recaptcha("token")


def test_an_explicit_failure_is_rejected(enabled, monkeypatch):
    respond_with(monkeypatch, {"success": False, "error-codes": ["invalid-input-response"]})

    with pytest.raises(HTTPException) as raised:
        verify_recaptcha("token")
    assert raised.value.status_code == 400


def test_a_token_minted_for_another_action_is_rejected(enabled, monkeypatch):
    """The site key is public, so a token can be minted anywhere. Tying it to the action stops a
    token from a low-value page being replayed against registration."""
    respond_with(monkeypatch, {"success": True, "score": 0.9, "action": "newsletter"})

    with pytest.raises(HTTPException) as raised:
        verify_recaptcha("token", action="register")
    assert raised.value.status_code == 400


def test_a_matching_action_passes(enabled, monkeypatch):
    respond_with(monkeypatch, {"success": True, "score": 0.9, "action": "register"})
    verify_recaptcha("token", action="register")


def test_a_v2_response_with_no_score_passes_on_success(enabled, monkeypatch):
    """v2 returns no score field; success alone is the verdict."""
    respond_with(monkeypatch, {"success": True})
    verify_recaptcha("token")


@pytest.mark.parametrize(
    "error",
    [
        httpx.TimeoutException("timed out"),
        httpx.ConnectError("refused"),
        httpx.HTTPError("boom"),
    ],
)
def test_transport_failures_fail_open(enabled, monkeypatch, error):
    """Google being unreachable must not take the site down. The rate limit is the backstop."""
    raise_with(monkeypatch, error)
    verify_recaptcha("token")


def test_a_non_json_body_fails_open(enabled, monkeypatch):
    """An HTML error page from a proxy is a transport problem, not a verdict."""
    respond_with(monkeypatch, ValueError("not json"))
    verify_recaptcha("token")


def test_the_secret_is_sent_and_the_timeout_is_applied(enabled, monkeypatch):
    monkeypatch.setattr(recaptcha.settings, "recaptcha_timeout_seconds", 2.5)
    calls = respond_with(monkeypatch, {"success": True, "score": 0.9})

    verify_recaptcha("the-token", action="register")

    url, kwargs = calls[0]
    assert url == recaptcha.VERIFY_URL
    assert kwargs["data"] == {"secret": "test-secret", "response": "the-token"}
    assert kwargs["timeout"] == 2.5
