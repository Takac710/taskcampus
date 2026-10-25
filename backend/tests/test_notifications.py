from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import notifications
from app.database import Base
from app.models import PushSubscription, Task, TaskStatus, TaskType, User

NOW = datetime(2026, 10, 26, 9, 0)  # a Monday, 9:00 JST


@pytest.fixture
def db():
    # Isolated in-memory DB per test -- the app-wide SessionLocal is a single
    # shared file across the whole test session, which would let one test's
    # not-yet-notified tasks get swept up by another test's sweep() call.
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def user(db):
    u = User(google_sub="notif-test-user", name="通知テストユーザー")
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def subscribed_user(db, user):
    db.add(
        PushSubscription(
            user_id=user.id,
            endpoint="https://example.com/push/subscription",
            p256dh="p256dh-value",
            auth="auth-value",
        )
    )
    db.commit()
    return user


@pytest.fixture(autouse=True)
def _fake_webpush(monkeypatch):
    calls = []
    monkeypatch.setattr(notifications, "webpush", lambda **kwargs: calls.append(kwargs))
    return calls


def _make_task(db, user, due_at, **overrides) -> Task:
    fields = {
        "user_id": user.id,
        "title": "第3回レポート",
        "type": TaskType.report,
        "due_at": due_at,
        "status": TaskStatus.open,
    }
    fields.update(overrides)
    task = Task(**fields)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def test_sends_24h_reminder_once(db, subscribed_user, _fake_webpush):
    task = _make_task(db, subscribed_user, due_at=datetime(2026, 10, 27, 8, 0))  # 23h away

    notifications.run_reminder_sweep(db, now=NOW)
    db.refresh(task)
    assert task.notified_24h_at == NOW
    assert len(_fake_webpush) == 1

    notifications.run_reminder_sweep(db, now=NOW)
    assert len(_fake_webpush) == 1  # not sent twice


def test_no_24h_reminder_outside_window(db, subscribed_user, _fake_webpush):
    task = _make_task(db, subscribed_user, due_at=datetime(2026, 10, 30, 8, 0))  # far away

    notifications.run_reminder_sweep(db, now=NOW)
    db.refresh(task)
    assert task.notified_24h_at is None
    assert len(_fake_webpush) == 0


def test_sends_morning_of_reminder(db, subscribed_user, _fake_webpush):
    # 24h-before already handled earlier, so this run exercises the morning check only.
    task = _make_task(
        db, subscribed_user, due_at=datetime(2026, 10, 26, 23, 59), notified_24h_at=NOW
    )

    notifications.run_reminder_sweep(db, now=NOW)  # 09:00, past the 08:00 cutoff
    db.refresh(task)
    assert task.notified_morning_at == NOW
    assert len(_fake_webpush) == 1


def test_no_morning_reminder_before_8am(db, subscribed_user, _fake_webpush):
    task = _make_task(
        db, subscribed_user, due_at=datetime(2026, 10, 26, 23, 59), notified_24h_at=NOW
    )
    early = NOW.replace(hour=7, minute=0)

    notifications.run_reminder_sweep(db, now=early)
    db.refresh(task)
    assert task.notified_morning_at is None
    assert len(_fake_webpush) == 0


def test_both_reminders_fire_independently_for_a_same_day_task(db, subscribed_user, _fake_webpush):
    """A task due later today, checked after 8am, is both <24h away and due
    today -- both reminder kinds should fire, as two separate notifications."""
    task = _make_task(db, subscribed_user, due_at=datetime(2026, 10, 26, 23, 59))

    notifications.run_reminder_sweep(db, now=NOW)
    db.refresh(task)
    assert task.notified_24h_at == NOW
    assert task.notified_morning_at == NOW
    assert len(_fake_webpush) == 2


def test_no_reminder_without_subscription(db, user, _fake_webpush):
    task = _make_task(db, user, due_at=datetime(2026, 10, 27, 8, 0))

    notifications.run_reminder_sweep(db, now=NOW)
    db.refresh(task)
    # still marked as notified (nothing to retry) even though there was no
    # subscription to actually push to
    assert task.notified_24h_at == NOW
    assert len(_fake_webpush) == 0


def test_done_task_is_not_notified(db, subscribed_user, _fake_webpush):
    task = _make_task(
        db, subscribed_user, due_at=datetime(2026, 10, 27, 8, 0), status=TaskStatus.done
    )

    notifications.run_reminder_sweep(db, now=NOW)
    db.refresh(task)
    assert task.notified_24h_at is None
    assert len(_fake_webpush) == 0
