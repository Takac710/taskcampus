from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("", response_model=list[schemas.CourseOut])
def list_courses(
    include_archived: bool = False,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    query = db.query(models.Course).filter(models.Course.user_id == user.id)
    if not include_archived:
        query = query.filter(models.Course.archived.is_(False))
    return query.order_by(models.Course.name).all()


@router.post("", response_model=schemas.CourseOut, status_code=201)
def create_course(
    payload: schemas.CourseCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    course = models.Course(user_id=user.id, name=payload.name, color=payload.color)
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


def _get_owned_course(course_id: str, db: Session, user: models.User) -> models.Course:
    course = (
        db.query(models.Course)
        .filter(models.Course.id == course_id, models.Course.user_id == user.id)
        .first()
    )
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.patch("/{course_id}", response_model=schemas.CourseOut)
def update_course(
    course_id: str,
    payload: schemas.CourseUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    course = _get_owned_course(course_id, db, user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(course, field, value)
    db.commit()
    db.refresh(course)
    return course


@router.delete("/{course_id}", status_code=204)
def delete_course(
    course_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    course = _get_owned_course(course_id, db, user)
    db.delete(course)
    db.commit()
