"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { RequireAuth } from "@/components/RequireAuth";
import { api } from "@/lib/api";
import type { Course, Task, TaskType } from "@/lib/types";
import { TASK_TYPE_LABEL } from "@/lib/types";

const TASK_TYPES: TaskType[] = ["report", "quiz", "presentation", "other"];

function toDatetimeLocal(iso: string | null): string {
  if (!iso) return "";
  return iso.slice(0, 16);
}

function fromDatetimeLocal(value: string): string | null {
  return value ? `${value}:00` : null;
}

function TaskDetailContent() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [task, setTask] = useState<Task | null>(null);
  const [courses, setCourses] = useState<Course[]>([]);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.getTask(id), api.listCourses(true)])
      .then(([t, c]) => {
        setTask(t);
        setCourses(c);
      })
      .catch(() => setError("タスクの読み込みに失敗しました"));
  }, [id]);

  if (error) return <p className="p-4 text-sm text-red-600">{error}</p>;
  if (!task) return <p className="p-4 text-sm text-neutral-500">読み込み中...</p>;

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await api.updateTask(task.id, {
        title: task.title,
        course_id: task.course_id,
        type: task.type,
        due_at: task.due_at,
        memo: task.memo,
        status: task.status,
      });
      router.push("/");
    } catch {
      setError("保存に失敗しました");
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm("このタスクを削除しますか？")) return;
    await api.deleteTask(task.id);
    router.push("/");
  };

  return (
    <div className="mx-auto max-w-2xl px-4 pb-24 pt-4">
      <h1 className="text-xl font-bold">タスク編集</h1>

      <div className="mt-4 space-y-4 rounded-lg border border-neutral-200 bg-white p-4">
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={task.status === "done"}
            onChange={(e) => setTask({ ...task, status: e.target.checked ? "done" : "open" })}
            className="h-5 w-5 accent-indigo-600"
          />
          完了にする
        </label>

        <div>
          <label className="block text-xs font-medium text-neutral-500">タイトル</label>
          <input
            value={task.title}
            onChange={(e) => setTask({ ...task, title: e.target.value })}
            className="mt-1 w-full rounded border border-neutral-300 px-3 py-2 text-sm"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-neutral-500">科目</label>
          <select
            value={task.course_id ?? ""}
            onChange={(e) => setTask({ ...task, course_id: e.target.value || null })}
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
            value={task.type}
            onChange={(e) => setTask({ ...task, type: e.target.value as TaskType })}
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
          <label className="block text-xs font-medium text-neutral-500">締切</label>
          <input
            type="datetime-local"
            value={toDatetimeLocal(task.due_at)}
            onChange={(e) => setTask({ ...task, due_at: fromDatetimeLocal(e.target.value) })}
            className="mt-1 w-full rounded border border-neutral-300 px-3 py-2 text-sm"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-neutral-500">メモ</label>
          <textarea
            value={task.memo}
            onChange={(e) => setTask({ ...task, memo: e.target.value })}
            rows={3}
            className="mt-1 w-full rounded border border-neutral-300 px-3 py-2 text-sm"
          />
        </div>
      </div>

      <div className="mt-4 flex gap-2">
        <button
          onClick={handleDelete}
          className="rounded border border-red-300 px-4 py-2 text-sm font-medium text-red-600"
        >
          削除
        </button>
        <button
          onClick={handleSave}
          disabled={isSaving}
          className="flex-1 rounded bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {isSaving ? "保存中..." : "保存"}
        </button>
      </div>
    </div>
  );
}

export default function TaskDetailPage() {
  return (
    <RequireAuth>
      <TaskDetailContent />
    </RequireAuth>
  );
}
