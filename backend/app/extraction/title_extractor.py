"""Heuristic title cleanup: strip matched date/time spans, the matched course name,
and common Japanese submission-instruction boilerplate, leaving the task name.
"""

import re

# Deadline connector -- removed wherever it appears, not just at the string's edge,
# since stripping the matched date/time span first tends to leave "までに" stranded
# mid-sentence (e.g. "来週の月曜までにレポート" -> "のまでにレポート" once "来週"/"月曜" go).
_INFIX_PATTERNS = [r"までに", r"まで"]

_TRAILING_PATTERNS = [
    r"を?提出してください",
    r"してください",
    r"提出のこと",
    r"お願いします",
    r"を?提出$",
]

_STRIP_CHARS = " 、。のをはがに\n\t"


def extract_title(sentence: str, time_spans: list[str], course_name: str | None) -> str:
    cleaned = sentence
    for span in time_spans:
        if span:
            cleaned = cleaned.replace(span, "")
    if course_name:
        cleaned = cleaned.replace(course_name, "")
    for pattern in _INFIX_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned)
    for pattern in _TRAILING_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned)
    cleaned = re.sub(r"の+", "の", cleaned)
    cleaned = cleaned.strip(_STRIP_CHARS)
    return cleaned or sentence.strip()
