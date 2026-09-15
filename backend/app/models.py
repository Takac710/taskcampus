import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    # Naive UTC on purpose: SQLite (the local/dev DB) doesn't persist tzinfo, so
    # mixing aware and naive datetimes here would raise on comparison later.
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TaskType(str, enum.Enum):
    report = "report"
    quiz = "quiz"
    presentation = "presentation"
    other = "other"


class TaskStatus(str, enum.Enum):
    open = "open"
    done = "done"


class TaskSource(str, enum.Enum):
    manual = "manual"
    paste = "paste"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    google_sub: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    courses: Mapped[list["Course"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    tasks: Mapped[list["Task"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    color: Mapped[str] = mapped_column(String(16), default="#4F46E5")
    archived: Mapped[bool] = mapped_column(default=False)

    user: Mapped[User] = relationship(back_populates="courses")
    tasks: Mapped[list["Task"]] = relationship(back_populates="course")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    course_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("courses.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(500))
    type: Mapped[TaskType] = mapped_column(Enum(TaskType), default=TaskType.other)
    due_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    memo: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.open)
    source: Mapped[TaskSource] = mapped_column(Enum(TaskSource), default=TaskSource.manual)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    user: Mapped[User] = relationship(back_populates="tasks")
    course: Mapped[Course | None] = relationship(back_populates="tasks")


class ExtractionLog(Base):
    __tablename__ = "extraction_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    raw_text: Mapped[str] = mapped_column(Text)
    extracted_json: Mapped[dict] = mapped_column(JSON)
    corrected_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
