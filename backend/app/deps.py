"""Auth dependency.

MVP note: real auth is delegated to Supabase (Google OAuth) per the requirements
doc. Wiring that up needs a Supabase project the user creates outside this repo.
Until then, every request resolves to a single dev user so the rest of the app
(CRUD, extraction) can be built and tested end-to-end. Swap `get_current_user`'s
body for real Supabase JWT verification when credentials exist -- callers
elsewhere never need to change.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from .config import get_settings
from .database import get_db
from .models import User

settings = get_settings()


def get_current_user(db: Session = Depends(get_db)) -> User:
    user = db.query(User).filter(User.google_sub == settings.dev_user_google_sub).first()
    if user is None:
        user = User(google_sub=settings.dev_user_google_sub, name="開発ユーザー")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user
