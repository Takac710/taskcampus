from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user
from ..extraction import run_extraction

router = APIRouter(prefix="/extract", tags=["extract"])


@router.post("", response_model=schemas.ExtractResponse)
def extract(
    payload: schemas.ExtractRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """F-03: paste free text, get back a best-effort {course, title, due_at, type}
    guess for the user to confirm/edit before it becomes a task."""
    courses = (
        db.query(models.Course.id, models.Course.name)
        .filter(models.Course.user_id == user.id, models.Course.archived.is_(False))
        .all()
    )
    fields = run_extraction(payload.raw_text, [(c.id, c.name) for c in courses])

    log = models.ExtractionLog(
        user_id=user.id,
        raw_text=payload.raw_text,
        extracted_json=fields.model_dump(mode="json"),
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    return schemas.ExtractResponse(extraction_log_id=log.id, fields=fields)


@router.post("/confirm", response_model=schemas.TaskOut, status_code=201)
def confirm(
    payload: schemas.ExtractConfirm,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """F-03: user reviewed (and possibly corrected) the extraction; log the
    correction for future rule/dictionary tuning and create the real task."""
    log = (
        db.query(models.ExtractionLog)
        .filter(models.ExtractionLog.id == payload.extraction_log_id, models.ExtractionLog.user_id == user.id)
        .first()
    )
    if log is None:
        raise HTTPException(status_code=404, detail="Extraction log not found")

    log.corrected_json = payload.fields.model_dump(mode="json")
    db.commit()

    task = models.Task(
        user_id=user.id,
        course_id=payload.fields.course_id,
        title=payload.fields.title,
        type=payload.fields.type,
        due_at=payload.fields.due_at,
        source=models.TaskSource.paste,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task
