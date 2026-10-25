"""Orchestrates the "貼るだけ登録" extraction: no external LLM call, just the
rule-based ja-timex/RapidFuzz/dictionary layers below, composed here.
"""

from datetime import datetime

from ..schemas import ExtractedFields
from ..time_utils import now_jst
from .course_matcher import match_course
from .time_parser import resolve_due_datetime
from .title_extractor import extract_title
from .type_classifier import classify_type


def run_extraction(
    text: str,
    courses: list[tuple[str, str]],
    now: datetime | None = None,
) -> ExtractedFields:
    now = now or now_jst()
    first_sentence = text.split("。")[0] if text.strip() else text

    time_result = resolve_due_datetime(text, now=now)
    time_spans = time_result.matched_spans

    course_match = match_course(text, courses)
    task_type = classify_type(text)
    matched_course_name = course_match.course_name if course_match.course_id else None
    title = extract_title(first_sentence, time_spans, matched_course_name)

    return ExtractedFields(
        course_id=course_match.course_id,
        course_name_guess=course_match.course_name,
        course_confidence=course_match.confidence,
        title=title,
        due_at=time_result.due_at,
        due_text_matched=time_result.matched_text,
        type=task_type,
    )
