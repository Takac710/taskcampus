from datetime import datetime

from pydantic import BaseModel, ConfigDict

from .models import TaskSource, TaskStatus, TaskType


class CourseBase(BaseModel):
    name: str
    color: str = "#4F46E5"


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    name: str | None = None
    color: str | None = None
    archived: bool | None = None


class CourseOut(CourseBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    archived: bool


class TaskBase(BaseModel):
    title: str
    course_id: str | None = None
    type: TaskType = TaskType.other
    due_at: datetime | None = None
    memo: str = ""


class TaskCreate(TaskBase):
    source: TaskSource = TaskSource.manual


class TaskUpdate(BaseModel):
    title: str | None = None
    course_id: str | None = None
    type: TaskType | None = None
    due_at: datetime | None = None
    memo: str | None = None
    status: TaskStatus | None = None


class TaskOut(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: TaskStatus
    source: TaskSource
    created_at: datetime


class ExtractRequest(BaseModel):
    raw_text: str


class ExtractedFields(BaseModel):
    course_id: str | None = None
    course_name_guess: str | None = None
    course_confidence: float = 0.0
    title: str
    due_at: datetime | None = None
    due_text_matched: str | None = None
    type: TaskType = TaskType.other


class ExtractResponse(BaseModel):
    extraction_log_id: str
    fields: ExtractedFields


class ExtractConfirm(BaseModel):
    extraction_log_id: str
    fields: ExtractedFields
