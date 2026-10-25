"""Web Push reminders (M6, F-05): 24h-before and day-of-8am-JST nudges.

Runs as a periodic in-process sweep (see main.py's scheduler) rather than
the requirements doc's eventual Supabase pg_cron + Edge Functions setup --
that migration is deploy-stage work (Render's free tier sleeps when idle,
so cron needs to live outside it) and isn't needed while the app only
runs locally.
"""

import json
import logging
from datetime import datetime, timedelta

from pywebpush import WebPushException, webpush
from sqlalchemy.orm import Session

from .config import get_settings
from .models import PushSubscription, Task, TaskStatus
from .time_utils import now_jst

logger = logging.getLogger(__name__)
settings = get_settings()

REMINDER_WINDOW_24H = timedelta(hours=24)
MORNING_HOUR = 8


def _send(db: Session, subscription: PushSubscription, payload: dict) -> None:
    try:
        webpush(
            subscription_info={
                "endpoint": subscription.endpoint,
                "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
            },
            data=json.dumps(payload),
            vapid_private_key=settings.vapid_private_key,
            vapid_claims={"sub": settings.vapid_subject},
        )
    except WebPushException as exc:
        status = exc.response.status_code if exc.response is not None else None
        if status in (404, 410):
            # Subscription is gone (browser data cleared, uninstalled, etc.) -- prune it.
            db.delete(subscription)
        else:
            logger.warning("push send failed for subscription %s: %s", subscription.id, exc)


def _notify_user(db: Session, user_id: str, payload: dict) -> None:
    subscriptions = db.query(PushSubscription).filter(PushSubscription.user_id == user_id).all()
    for subscription in subscriptions:
        _send(db, subscription, payload)


def run_reminder_sweep(db: Session, now: datetime | None = None) -> None:
    now = now or now_jst()
    today_8am = now.replace(hour=MORNING_HOUR, minute=0, second=0, microsecond=0)

    open_tasks = db.query(Task).filter(Task.status == TaskStatus.open, Task.due_at.isnot(None)).all()

    for task in open_tasks:
        due_at = task.due_at

        if task.notified_24h_at is None and now <= due_at <= now + REMINDER_WINDOW_24H:
            _notify_user(
                db,
                task.user_id,
                {"title": "締切24時間前", "body": task.title, "url": f"/tasks/{task.id}"},
            )
            task.notified_24h_at = now

        if task.notified_morning_at is None and due_at.date() == now.date() and now >= today_8am:
            _notify_user(
                db,
                task.user_id,
                {"title": "本日提出", "body": task.title, "url": f"/tasks/{task.id}"},
            )
            task.notified_morning_at = now

    db.commit()
