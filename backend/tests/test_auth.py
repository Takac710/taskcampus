import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import HTTPException
from jose import jwk, jwt

from app import deps

SECRET = "unit-test-secret"


@pytest.fixture(autouse=True)
def _secret(monkeypatch):
    monkeypatch.setattr(deps.settings, "supabase_jwt_secret", SECRET)


def _sign_hs256(payload: dict, secret: str = SECRET) -> str:
    return jwt.encode(payload, secret, algorithm="HS256")


def test_decode_accepts_valid_hs256_token():
    """Older/legacy-mode Supabase projects sign every token with the shared secret."""
    token = _sign_hs256({"sub": "user-123", "aud": "authenticated"})
    payload = deps._decode_token(token)
    assert payload["sub"] == "user-123"


def test_decode_rejects_wrong_secret():
    token = _sign_hs256({"sub": "user-123", "aud": "authenticated"}, secret="wrong-secret")
    with pytest.raises(HTTPException) as exc_info:
        deps._decode_token(token)
    assert exc_info.value.status_code == 401


def test_decode_rejects_wrong_audience():
    token = _sign_hs256({"sub": "user-123", "aud": "some-other-app"})
    with pytest.raises(HTTPException):
        deps._decode_token(token)


@pytest.fixture
def ec_keypair():
    """An EC key pair plus its JWKS entry, mimicking the asymmetric signing
    keys newer Supabase projects use by default instead of the legacy secret."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_jwk = jwk.construct(pem, algorithm="ES256").to_dict()
    public_jwk.pop("d", None)
    public_jwk["kid"] = "test-kid"
    return pem, public_jwk


def test_decode_accepts_valid_jwks_token(ec_keypair, monkeypatch):
    pem, public_jwk = ec_keypair
    monkeypatch.setattr(deps, "get_jwks", lambda: {"keys": [public_jwk]})

    token = jwt.encode(
        {"sub": "user-456", "aud": "authenticated"},
        pem,
        algorithm="ES256",
        headers={"kid": "test-kid"},
    )
    payload = deps._decode_token(token)
    assert payload["sub"] == "user-456"


def test_decode_rejects_jwks_token_with_no_matching_key(ec_keypair, monkeypatch):
    pem, _public_jwk = ec_keypair
    monkeypatch.setattr(deps, "get_jwks", lambda: {"keys": []})

    token = jwt.encode(
        {"sub": "user-456", "aud": "authenticated"},
        pem,
        algorithm="ES256",
        headers={"kid": "test-kid"},
    )
    with pytest.raises(HTTPException) as exc_info:
        deps._decode_token(token)
    assert exc_info.value.status_code == 401
