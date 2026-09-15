"""Resolves Japanese relative/absolute deadline expressions to an absolute datetime.

ja-timex annotates spans with raw TIMEX3-style tags (DURATION/DATE/TIME) but does not
itself resolve them to a concrete datetime -- e.g. "来週水曜日" comes back as a
DURATION("来週", +1 week) tag plus a separate DATE("水曜日", weekday=3) tag. This module
is the rule-based resolution layer described in the requirements doc: it combines those
tags (plus a few patterns ja-timex misses, like "正午" or "◯月末") against a reference
"now" to produce one due_at.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from ja_timex import TimexParser

_parser = TimexParser()

_WEEKDAY_JA_TO_INDEX = {"月": 0, "火": 1, "水": 2, "木": 3, "金": 4, "土": 5, "日": 6}

_NOON_RE_TEXT = "正午"
_LAST_DAY_MARKER = "末"


@dataclass
class TimeParseResult:
    due_at: datetime | None
    matched_text: str | None
    matched_spans: list[str]


def _week_monday(d: datetime) -> datetime:
    return (d - timedelta(days=d.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)


def _last_day_of_month(year: int, month: int) -> int:
    next_month_first = datetime(year + (month // 12), (month % 12) + 1, 1)
    return (next_month_first - timedelta(days=1)).day


def _to_int(value: str | None) -> int | None:
    if value is None or "X" in value:
        return None
    return int(value)


def resolve_due_datetime(text: str, now: datetime | None = None) -> TimeParseResult:
    now = now or datetime.now()
    timexes = _parser.parse(text)

    week_offset: int | None = None
    day_offset: int | None = None
    month_offset: int | None = None
    weekday_index: int | None = None
    abs_month = abs_day = None
    hour = minute = None
    matched: list[str] = []

    for tx in timexes:
        parsed = tx.parsed or {}
        if tx.type == "DURATION":
            if "week" in parsed:
                week_offset = int(parsed["week"])
                matched.append(tx.raw_text)
            elif "month" in parsed:
                month_offset = int(parsed["month"])
                matched.append(tx.raw_text)
            elif "day" in parsed:
                day_offset = int(parsed["day"])
                matched.append(tx.raw_text)
        elif tx.type == "DATE":
            if "weekday" in parsed:
                weekday_index = _WEEKDAY_JA_TO_INDEX[parsed["weekday"]]
                matched.append(tx.raw_text)
            else:
                month = _to_int(parsed.get("calendar_month"))
                day = _to_int(parsed.get("calendar_day"))
                if month and day:
                    abs_month, abs_day = month, day
                    matched.append(tx.raw_text)
        elif tx.type == "TIME":
            h = _to_int(parsed.get("clock_hour"))
            if h is not None:
                hour = h
                if parsed.get("pm_prefix") and hour < 12:
                    hour += 12
                m = _to_int(parsed.get("clock_minute"))
                minute = 30 if parsed.get("half_suffix") else (m or 0)
                matched.append(tx.raw_text)

    if hour is None and _NOON_RE_TEXT in text:
        hour, minute = 12, 0
        matched.append(_NOON_RE_TEXT)

    date_part: datetime | None = None

    if abs_month and abs_day:
        candidate = now.replace(month=abs_month, day=abs_day, hour=0, minute=0, second=0, microsecond=0)
        if candidate.date() < now.date():
            candidate = candidate.replace(year=candidate.year + 1)
        date_part = candidate
    elif week_offset is not None and weekday_index is not None:
        date_part = _week_monday(now) + timedelta(weeks=week_offset, days=weekday_index)
    elif weekday_index is not None:
        delta = (weekday_index - now.weekday()) % 7
        date_part = (now + timedelta(days=delta)).replace(hour=0, minute=0, second=0, microsecond=0)
    elif month_offset is not None:
        target_month_0based = now.month - 1 + month_offset
        target_year = now.year + target_month_0based // 12
        target_month = target_month_0based % 12 + 1
        last_day = _last_day_of_month(target_year, target_month)
        is_month_end = _LAST_DAY_MARKER in text
        day = last_day if is_month_end else min(now.day, last_day)
        date_part = datetime(target_year, target_month, day)
        if is_month_end:
            matched.append(_LAST_DAY_MARKER)
    elif day_offset is not None:
        date_part = (now + timedelta(days=day_offset)).replace(hour=0, minute=0, second=0, microsecond=0)
    elif week_offset is not None:
        date_part = _week_monday(now) + timedelta(weeks=week_offset)

    if date_part is None:
        return TimeParseResult(due_at=None, matched_text=None, matched_spans=matched)

    if hour is not None:
        due_at = date_part.replace(hour=hour, minute=minute or 0, second=0, microsecond=0)
    else:
        due_at = date_part.replace(hour=23, minute=59, second=0, microsecond=0)

    return TimeParseResult(due_at=due_at, matched_text="".join(matched), matched_spans=matched)
