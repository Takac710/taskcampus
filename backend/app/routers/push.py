from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..config import get_settings
from ..database import get_db
from ..deps import get_current_user

router = APIRouter(prefix="/push", tags=["push"])
settings = get_settings()


@router.get("/vapid-public-key")
def vapid_public_key():
    return {"public_key": settings.vapid_public_key}


@router.post("/subscriptions", status_code=201)
def create_subscription(
    payload: schemas.PushSubscriptionCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Upserts by endpoint so re-subscribing (e.g. after permission is
    re-granted) updates the keys instead of creating a duplicate row."""
    subscription = (
        db.query(models.PushSubscription)
        .filter(models.PushSubscription.endpoint == payload.endpoint)
        .first()
    )
    if subscription is None:
        subscription = models.PushSubscription(user_id=user.id, endpoint=payload.endpoint)
        db.add(subscription)

    subscription.user_id = user.id
    subscription.p256dh = payload.keys.p256dh
    subscription.auth = payload.keys.auth
    db.commit()
    return {"status": "ok"}
