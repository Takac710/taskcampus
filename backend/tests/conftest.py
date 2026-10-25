import os
from pathlib import Path

_TEST_DB_PATH = Path(__file__).parent / "test_taskcampus.db"
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_TEST_DB_PATH}")

import pytest

from app.database import SessionLocal
from app.deps import get_current_user
from app.main import app
from app.models import User


def _test_user() -> User:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.google_sub == "test-user").first()
        if user is None:
            user = User(google_sub="test-user", name="テストユーザー")
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def _override_auth():
    app.dependency_overrides[get_current_user] = _test_user
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture(scope="session", autouse=True)
def _cleanup_test_db():
    yield
    if _TEST_DB_PATH.exists():
        _TEST_DB_PATH.unlink()
