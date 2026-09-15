import os
from pathlib import Path

_TEST_DB_PATH = Path(__file__).parent / "test_taskcampus.db"
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_TEST_DB_PATH}")

import pytest


@pytest.fixture(scope="session", autouse=True)
def _cleanup_test_db():
    yield
    if _TEST_DB_PATH.exists():
        _TEST_DB_PATH.unlink()
