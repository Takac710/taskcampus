"""Auth dependency.

Verifies the Supabase Auth JWT sent by the frontend as `Authorization: Bearer
<token>` and resolves (or lazily creates) the corresponding local User row.
Supabase signs Auth tokens one of two ways depending on the project: the
legacy shared HS256 secret (Project Settings > API > JWT Settings), or --
the default for newer projects -- an asymmetric key pair, verified against
the project's published JWKS. We branch on the token's own `alg` header
rather than guessing, so this works either way.
"""

import logging

import httpx
from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from .config import get_settings
from .database import get_db
from .models import User
from .supabase_jwks import get_jwks

logger = logging.getLogger(__name__)
settings = get_settings()

AUDIENCE = "authenticated"
JWKS_ALGORITHMS = ["RS256", "ES256"]


def _decode_token(token: str) -> dict:
    try:
        alg = jwt.get_unverified_header(token).get("alg")
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token"
        ) from exc

    try:
        if alg == "HS256":
            return jwt.decode(
                token, settings.supabase_jwt_secret, algorithms=["HS256"], audience=AUDIENCE
            )
        return jwt.decode(token, get_jwks(), algorithms=JWKS_ALGORITHMS, audience=AUDIENCE)
    except (JWTError, httpx.HTTPError) as exc:
        logger.warning("JWT decode failed: %r", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid or expired token"
        ) from exc


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token"
        )

    payload = _decode_token(authorization.split(" ", 1)[1])
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="token missing sub claim"
        )

    user = db.query(User).filter(User.google_sub == sub).first()
    if user is None:
        metadata = payload.get("user_metadata") or {}
        name = metadata.get("full_name") or metadata.get("name") or payload.get("email") or "ユーザー"
        user = User(google_sub=sub, name=name)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user
