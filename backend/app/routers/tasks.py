from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user
from ..time_utils import now_jst

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[schemas.TaskOut])
def list_tasks(
    status: models.TaskStatus | None = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    query = db.query(models.Task).filter(models.Task.user_id == user.id)
    if status is not None:
        query = query.filter(models.Task.status == status)
    return query.order_by(models.Task.due_at.is_(None), models.Task.due_at).all()


@router.post("", response_model=schemas.TaskOut, status_code=201)
def create_task(
    payload: schemas.TaskCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    task = models.Task(user_id=user.id, **payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def _get_owned_task(task_id: str, db: Session, user: models.User) -> models.Task:
    task = (
        db.query(models.Task)
        .filter(models.Task.id == task_id, models.Task.user_id == user.id)
        .first()
    )
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/{task_id}", response_model=schemas.TaskOut)
def get_task(
    task_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    return _get_owned_task(task_id, db, user)


@router.patch("/{task_id}", response_model=schemas.TaskOut)
def update_task(
    task_id: str,
    payload: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    task = _get_owned_task(task_id, db, user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=204)
def delete_task(
    task_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    task = _get_owned_task(task_id, db, user)
    db.delete(task)
    db.commit()


@router.get("/views/deadline-buckets")
def deadline_buckets(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Backs the home screen: overdue / today / this week / later, per F-04."""
    now = now_jst()
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=0)
    days_until_week_end = 6 - now.weekday()
    week_cutoff = (now + timedelta(days=days_until_week_end)).replace(hour=23, minute=59, second=59)

    open_tasks = (
        db.query(models.Task)
        .filter(models.Task.user_id == user.id, models.Task.status == models.TaskStatus.open)
        .order_by(models.Task.due_at.is_(None), models.Task.due_at)
        .all()
    )

    buckets = {"overdue": [], "today": [], "this_week": [], "later": [], "no_due_date": []}
    for task in open_tasks:
        if task.due_at is None:
            buckets["no_due_date"].append(task)
        elif task.due_at < now:
            buckets["overdue"].append(task)
        elif task.due_at <= today_end:
            buckets["today"].append(task)
        elif task.due_at <= week_cutoff:
            buckets["this_week"].append(task)
        else:
            buckets["later"].append(task)

    return {key: [schemas.TaskOut.model_validate(t) for t in tasks] for key, tasks in buckets.items()}
