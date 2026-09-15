"use client";

import { useEffect, useState } from "react";

import { RequireAuth } from "@/components/RequireAuth";
import { api } from "@/lib/api";
import type { Course } from "@/lib/types";

const COLOR_PRESETS = [
  "#4F46E5",
  "#DC2626",
  "#059669",
  "#D97706",
  "#7C3AED",
  "#0891B2",
  "#DB2777",
  "#65A30D",
];

function CoursesContent() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [name, setName] = useState("");
  const [color, setColor] = useState(COLOR_PRESETS[0]);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    const list = await api.listCourses();
    setCourses(list);
  };

  useEffect(() => {
    load();
  }, []);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    try {
      await api.createCourse({ name: name.trim(), color });
      setName("");
      setColor(COLOR_PRESETS[(courses.length + 1) % COLOR_PRESETS.length]);
      load();
    } catch {
      setError("科目の追加に失敗しました");
    }
  };

  const handleArchive = async (course: Course) => {
    await api.updateCourse(course.id, { archived: !course.archived });
    load();
  };

  const handleDelete = async (course: Course) => {
    if (!confirm(`「${course.name}」を削除しますか？紐づくタスクの科目表示も外れます。`)) return;
    await api.deleteCourse(course.id);
    load();
  };

  return (
    <div className="mx-auto max-w-2xl px-4 pb-24 pt-4">
      <h1 className="text-xl font-bold">科目管理</h1>

      <form onSubmit={handleAdd} className="mt-4 flex flex-wrap items-center gap-2 rounded-lg border border-neutral-200 bg-white p-3">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="科目名（例：データベース論）"
          className="min-w-0 flex-1 rounded border border-neutral-300 px-3 py-2 text-sm"
        />
        <div className="flex gap-1">
          {COLOR_PRESETS.map((c) => (
            <button
              type="button"
              key={c}
              onClick={() => setColor(c)}
              className={`h-6 w-6 rounded-full ${color === c ? "ring-2 ring-offset-1 ring-neutral-900" : ""}`}
              style={{ backgroundColor: c }}
              aria-label={`色 ${c}`}
            />
          ))}
        </div>
        <button
          type="submit"
          className="rounded bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
        >
          追加
        </button>
      </form>

      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}

      <div className="mt-4 rounded-lg border border-neutral-200 bg-white">
        {courses.map((course) => (
          <div
            key={course.id}
            className="flex items-center gap-3 border-b border-neutral-100 px-4 py-3 last:border-b-0"
          >
            <span className="h-3 w-3 shrink-0 rounded-full" style={{ backgroundColor: course.color }} />
            <span className={`flex-1 text-sm ${course.archived ? "text-neutral-400 line-through" : ""}`}>
              {course.name}
            </span>
            <button onClick={() => handleArchive(course)} className="text-xs text-neutral-500 hover:underline">
              {course.archived ? "復元" : "アーカイブ"}
            </button>
            <button onClick={() => handleDelete(course)} className="text-xs text-red-500 hover:underline">
              削除
            </button>
          </div>
        ))}
        {courses.length === 0 && (
          <p className="px-4 py-6 text-center text-sm text-neutral-400">まだ科目がありません</p>
        )}
      </div>
    </div>
  );
}

export default function CoursesPage() {
  return (
    <RequireAuth>
      <CoursesContent />
    </RequireAuth>
  );
}
