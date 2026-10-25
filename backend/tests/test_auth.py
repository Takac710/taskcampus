import pytest
from fastapi import HTTPException
from jose import jwt

from app import deps

SECRET = "unit-test-secret"


@pytest.fixture(autouse=True)
def _secret(monkeypatch):
    monkeypatch.setattr(deps.settings, "supabase_jwt_secret", SECRET)


def _sign(payload: dict, secret: str = SECRET) -> str:
    return jwt.encode(payload, secret, algorithm=deps.ALGORITHM)


def test_decode_accepts_valid_supabase_token():
    token = _sign({"sub": "user-123", "aud": "authenticated"})
    payload = deps._decode_token(token)
    assert payload["sub"] == "user-123"


def test_decode_rejects_wrong_secret():
    token = _sign({"sub": "user-123", "aud": "authenticated"}, secret="wrong-secret")
    with pytest.raises(HTTPException) as exc_info:
        deps._decode_token(token)
    assert exc_info.value.status_code == 401


def test_decode_rejects_wrong_audience():
    token = _sign({"sub": "user-123", "aud": "some-other-app"})
    with pytest.raises(HTTPException):
        deps._decode_token(token)
