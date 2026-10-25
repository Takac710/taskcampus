"""Single source of truth for "now" in this app's date semantics.

`Task.due_at` is stored as a naive datetime representing Japan Standard
Time wall-clock time -- that's what the frontend's `<input type="datetime-
local">` and the extraction pipeline's relative-date resolution ("来週月
曜" etc.) both produce, since the target users are in Japan. Any code that
compares "now" against `due_at` must use `now_jst()` here rather than
`datetime.now()` (depends on the server OS timezone -- UTC once this runs
on Render) or `datetime.now(timezone.utc)` (wrong by the JST offset).
"""

from datetime import datetime
from zoneinfo import ZoneInfo

JST = ZoneInfo("Asia/Tokyo")


def now_jst() -> datetime:
    return datetime.now(JST).replace(tzinfo=None)
