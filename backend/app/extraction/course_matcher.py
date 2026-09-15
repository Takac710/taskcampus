"""Fuzzy-matches a course mentioned in free text against the user's registered courses.

Uses RapidFuzz partial-ratio so a course name that appears as a substring of a longer
sentence (the common case) still scores highly, and tolerates abbreviations / kana
spelling variants.
"""

from dataclasses import dataclass

from rapidfuzz import fuzz

DEFAULT_THRESHOLD = 60.0


@dataclass
class CourseMatch:
    course_id: str | None
    course_name: str | None
    confidence: float


def match_course(
    text: str,
    courses: list[tuple[str, str]],
    threshold: float = DEFAULT_THRESHOLD,
) -> CourseMatch:
    best_id: str | None = None
    best_name: str | None = None
    best_score = 0.0

    for course_id, name in courses:
        score = fuzz.partial_ratio(name, text)
        if score > best_score:
            best_score = score
            best_id, best_name = course_id, name

    confidence = round(best_score / 100, 2)
    if best_id is not None and best_score >= threshold:
        return CourseMatch(course_id=best_id, course_name=best_name, confidence=confidence)
    return CourseMatch(course_id=None, course_name=best_name, confidence=confidence)
