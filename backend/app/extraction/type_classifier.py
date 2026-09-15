"""Rule-based task-type classification via a keyword dictionary.

Dict order is the tie-break priority when a sentence contains more than one
keyword family (e.g. both "レポート" and "テスト").
"""

from ..models import TaskType

_KEYWORDS: dict[TaskType, list[str]] = {
    TaskType.report: ["レポート", "報告書", "小論文", "論文", "課題"],
    TaskType.quiz: ["小テスト", "テスト", "試験", "クイズ"],
    TaskType.presentation: ["発表", "プレゼン", "報告会"],
}


def classify_type(text: str) -> TaskType:
    for task_type, keywords in _KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return task_type
    return TaskType.other
