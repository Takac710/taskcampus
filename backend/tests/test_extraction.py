"""Accuracy test set for the paste-registration extraction pipeline (F-03).

The requirements doc calls for measuring exact-match accuracy on the three key
fields (course / title / due date) against a ~30-sentence test set, target 80%.
This is a starter set of 16 hand-written announcement-style sentences; extend it
as real paste examples come in (e.g. from `extraction_logs` once the app is used).

Two cases (13, 16) intentionally have no resolvable date -- a sentence that only
says "正午までに" / "深夜0時までに" with no day reference has no correct absolute
answer, so due_at=None (falling back to manual entry) *is* the correct output.
"""

from datetime import datetime

import pytest

from app.extraction.pipeline import run_extraction

NOW = datetime(2026, 9, 14, 9, 0)  # a Monday, used as "today" for every case below

COURSES = [
    ("c1", "データベース論"),
    ("c2", "機械学習"),
    ("c3", "英語コミュニケーション"),
    ("c4", "線形代数"),
    ("c5", "ソフトウェア工学"),
]

# (raw_text, expected_course_id, expected_due_at, expected_title_keyword)
CASES = [
    ("来週の月曜までにデータベース論のレポート第3回を提出してください", "c1", datetime(2026, 9, 21, 23, 59), "レポート"),
    ("機械学習の小テストは明日17時までに受験してください", "c2", datetime(2026, 9, 15, 17, 0), "小テスト"),
    ("線形代数の課題を9月20日までに提出してください", "c4", datetime(2026, 9, 20, 23, 59), "課題"),
    ("ソフトウェア工学のゼミ発表は来週水曜日正午までに資料を提出してください", "c5", datetime(2026, 9, 23, 12, 0), "発表"),
    ("英語コミュニケーションの試験は今週金曜日までに申し込んでください", "c3", datetime(2026, 9, 18, 23, 59), "試験"),
    ("データベース論のレポートを今日中に提出してください", "c1", datetime(2026, 9, 14, 23, 59), "レポート"),
    ("機械学習の課題は再来週の月曜までに提出のこと", "c2", datetime(2026, 9, 28, 23, 59), "課題"),
    ("線形代数のクイズは明後日23:59までに解答してください", "c4", datetime(2026, 9, 16, 23, 59), "クイズ"),
    ("ソフトウェア工学のレポートは今月末までに提出してください", "c5", datetime(2026, 9, 30, 23, 59), "レポート"),
    ("英語コミュニケーションの発表資料は来月末までに提出してください", "c3", datetime(2026, 10, 31, 23, 59), "発表"),
    ("データベース論の小テストは9/20 12:00までにオンラインで受験してください", "c1", datetime(2026, 9, 20, 12, 0), "小テスト"),
    ("機械学習のレポートは月曜日までに提出してください", "c2", datetime(2026, 9, 14, 23, 59), "レポート"),
    ("線形代数の発表は正午までに資料を提出してください", "c4", None, "発表"),
    ("来週の金曜日までに授業アンケートに回答してください", None, datetime(2026, 9, 25, 23, 59), "アンケート"),
    ("ソフトウェア工学のレポート提出は来週火曜17時半までに", "c5", datetime(2026, 9, 22, 17, 30), "レポート"),
    ("英語コミュニケーションのプレゼンは深夜0時までにアップロードしてください", "c3", None, "プレゼン"),
]


@pytest.mark.parametrize("raw_text,expected_course_id,expected_due_at,expected_title_keyword", CASES)
def test_extraction_case(raw_text, expected_course_id, expected_due_at, expected_title_keyword):
    fields = run_extraction(raw_text, COURSES, now=NOW)
    assert fields.course_id == expected_course_id, f"course mismatch for: {raw_text!r} -> {fields}"
    assert fields.due_at == expected_due_at, f"due_at mismatch for: {raw_text!r} -> {fields}"
    assert expected_title_keyword in fields.title, f"title mismatch for: {raw_text!r} -> {fields}"


def test_overall_accuracy_meets_target():
    """Mirrors the doc's KPI: >=80% exact match on all three key fields together."""
    hits = 0
    for raw_text, expected_course_id, expected_due_at, expected_title_keyword in CASES:
        fields = run_extraction(raw_text, COURSES, now=NOW)
        if (
            fields.course_id == expected_course_id
            and fields.due_at == expected_due_at
            and expected_title_keyword in fields.title
        ):
            hits += 1
    accuracy = hits / len(CASES)
    assert accuracy >= 0.8, f"accuracy {accuracy:.0%} below 80% target ({hits}/{len(CASES)})"
