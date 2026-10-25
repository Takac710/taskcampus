"""Auth dependency.

Verifies the Supabase Auth JWT sent by the frontend as `Authorization: Bearer
<token>` and resolves (or lazily creates) the corresponding local User row.
Supabase signs these tokens with the project's JWT secret (Project Settings >
API > JWT Settings > "Legacy JWT Secret" -- HS256) using the standard
`sub` (Supabase user id) and `aud: "authenticated"` claims.
"""

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from .config import get_settings
from .database import get_db
from .models import User

settings = get_settings()

ALGORITHM = "HS256"
AUDIENCE = "authenticated"


def _decode_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=[ALGORITHM],
            audience=AUDIENCE,
        )
    except JWTError as exc:
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
