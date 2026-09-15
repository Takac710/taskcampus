"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { RequireAuth } from "@/components/RequireAuth";
import { api } from "@/lib/api";
import type { Course, ExtractedFields, TaskType } from "@/lib/types";
import { TASK_TYPE_LABEL } from "@/lib/types";

const TASK_TYPES: TaskType[] = ["report", "quiz", "presentation", "other"];

function toDatetimeLocal(iso: string | null): string {
  if (!iso) return "";
  return iso.slice(0, 16);
}

function fromDatetimeLocal(value: string): string | null {
  return value ? `${value}:00` : null;
}

function PasteContent() {
  const router = useRouter();
  const [rawText, setRawText] = useState("");
  const [courses, setCourses] = useState<Course[]>([]);
  const [extractionLogId, setExtractionLogId] = useState<string | null>(null);
  const [fields, setFields] = useState<ExtractedFields | null>(null);
  const [isExtracting, setIsExtracting] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.listCourses().then(setCourses).catch(() => {});
  }, []);

  const handleExtract = async () => {
    if (!rawText.trim()) return;
    setIsExtracting(true);
    setError(null);
    try {
      const res = await api.extract(rawText);
      setExtractionLogId(res.extraction_log_id);
      setFields(res.fields);
    } catch {
      setError("抽出に失敗しました。手動で入力してください。");
      setExtractionLogId(null);
      setFields({
        course_id: null,
        course_name_guess: null,
        course_confidence: 0,
        title: "",
        due_at: null,
        due_text_matched: null,
        type: "other",
      });
    } finally {
      setIsExtracting(false);
    }
  };

  const handleConfirm = async () => {
    if (!fields) return;
    setIsSaving(true);
    setError(null);
    try {
      if (extractionLogId) {
        await api.confirmExtraction(extractionLogId, fields);
      } else {
        // No log id (extraction endpoint failed outright) -- create the task directly.
        await api.createTask({
          title: fields.title,
          course_id: fields.course_id,
          type: fields.type,
          due_at: fields.due_at,
          memo: "",
        });
      }
      router.push("/");
    } catch {
      setError("登録に失敗しました");
    } finally {
      setIsSaving(false);
    }
  };

  const handleBack = () => {
    setFields(null);
    setExtractionLogId(null);
  };

  if (fields) {
    return (
      <div className="mx-auto max-w-2xl px-4 pb-24 pt-4">
        <h1 className="text-xl font-bold">登録内容の確認</h1>
        <p className="mt-1 text-xs text-neutral-500">
          自動抽出した内容です。おかしいところは修正してから登録してください。
        </p>

        <div className="mt-4 space-y-4 rounded-lg border border-neutral-200 bg-white p-4">
          <div>
            <label className="block text-xs font-medium text-neutral-500">タイトル</label>
            <input
              value={fields.title}
              onChange={(e) => setFields({ ...fields, title: e.target.value })}
              className="mt-1 w-full rounded border border-neutral-300 px-3 py-2 text-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-neutral-500">
              科目
              {fields.course_id === null && fields.course_name_guess && (
                <span className="ml-2 text-amber-600">
                  候補「{fields.course_name_guess}」（自信度{Math.round(fields.course_confidence * 100)}%）を確認してください
                </span>
              )}
            </label>
            <select
              value={fields.course_id ?? ""}
              onChange={(e) => setFields({ ...fields, course_id: e.target.value || null })}
              className="mt-1 w-full rounded border border-neutral-300 px-3 py-2 text-sm"
            >
              <option value="">未設定</option>
              {courses.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-neutral-500">種類</label>
            <select
              value={fields.type}
              onChange={(e) => setFields({ ...fields, type: e.target.value as TaskType })}
              className="mt-1 w-full rounded border border-neutral-300 px-3 py-2 text-sm"
            >
              {TASK_TYPES.map((t) => (
                <option key={t} value={t}>
                  {TASK_TYPE_LABEL[t]}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-neutral-500">
              締切
              {!fields.due_at && (
                <span className="ml-2 text-amber-600">自動抽出できませんでした。手動で設定してください</span>
              )}
            </label>
            <input
              type="datetime-local"
              value={toDatetimeLocal(fields.due_at)}
              onChange={(e) => setFields({ ...fields, due_at: fromDatetimeLocal(e.target.value) })}
              className="mt-1 w-full rounded border border-neutral-300 px-3 py-2 text-sm"
            />
          </div>
        </div>

        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}

        <div className="mt-4 flex gap-2">
          <button
            onClick={handleBack}
            className="rounded border border-neutral-300 px-4 py-2 text-sm font-medium text-neutral-700"
          >
            戻る
          </button>
          <button
            onClick={handleConfirm}
            disabled={isSaving || !fields.title.trim()}
            className="flex-1 rounded bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {isSaving ? "登録中..." : "この内容で登録"}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl px-4 pb-24 pt-4">
      <h1 className="text-xl font-bold">貼り付け登録</h1>
      <p className="mt-1 text-xs text-neutral-500">
        Moodleやメール、LINEの課題連絡をそのまま貼り付けてください。科目・締切・種類を自動で読み取ります。
      </p>
      <textarea
        value={rawText}
        onChange={(e) => setRawText(e.target.value)}
        rows={8}
        placeholder="例：来週の月曜までにデータベース論のレポート第3回を提出してください"
        className="mt-4 w-full rounded-lg border border-neutral-300 p-3 text-sm"
      />
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      <button
        onClick={handleExtract}
        disabled={isExtracting || !rawText.trim()}
        className="mt-4 w-full rounded bg-indigo-600 px-4 py-3 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
      >
        {isExtracting ? "読み取り中..." : "読み取る"}
      </button>
    </div>
  );
}

export default function PastePage() {
  return (
    <RequireAuth>
      <PasteContent />
    </RequireAuth>
  );
}
