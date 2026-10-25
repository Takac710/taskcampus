"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { RequireAuth } from "@/components/RequireAuth";
import { TaskRow } from "@/components/TaskRow";
import { api } from "@/lib/api";
import { enablePushNotifications } from "@/lib/push";
import type { Course, DeadlineBuckets, Task } from "@/lib/types";

const SECTIONS: { key: keyof DeadlineBuckets; label: string; emphasize?: boolean }[] = [
  { key: "overdue", label: "期限切れ", emphasize: true },
  { key: "today", label: "今日" },
  { key: "this_week", label: "今週" },
  { key: "later", label: "それ以降" },
  { key: "no_due_date", label: "締切未設定" },
];

function HomeContent() {
  const [buckets, setBuckets] = useState<DeadlineBuckets | null>(null);
  const [courses, setCourses] = useState<Course[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notifPermission, setNotifPermission] = useState<NotificationPermission | null>(null);

  const load = async () => {
    try {
      const [b, c] = await Promise.all([api.deadlineBuckets(), api.listCourses(true)]);
      setBuckets(b);
      setCourses(c);
      setError(null);
    } catch {
      setError("読み込みに失敗しました。バックエンドが起動しているか確認してください。");
    }
  };

  useEffect(() => {
    load();
    if (typeof Notification !== "undefined") setNotifPermission(Notification.permission);
  }, []);

  const handleEnableNotifications = async () => {
    await enablePushNotifications();
    if (typeof Notification !== "undefined") setNotifPermission(Notification.permission);
  };

  const courseMap = new Map(courses.map((c) => [c.id, c]));

  const handleToggleDone = async (task: Task) => {
    await api.updateTask(task.id, { status: task.status === "done" ? "open" : "done" });
    load();
  };

  return (
    <div className="mx-auto max-w-2xl pb-24">
      <header className="flex items-center justify-between px-4 py-4">
        <h1 className="text-xl font-bold">今日やること</h1>
        <Link
          href="/paste"
          className="rounded-full bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700"
        >
          ＋ 貼り付け登録
        </Link>
      </header>

      {error && <p className="mx-4 rounded bg-red-50 p-3 text-sm text-red-600">{error}</p>}

      {notifPermission === "default" && (
        <div className="mx-4 flex items-center justify-between gap-3 rounded-lg bg-indigo-50 p-3 text-sm text-indigo-700">
          <span>締切の通知を受け取りますか？</span>
          <button
            onClick={handleEnableNotifications}
            className="shrink-0 rounded-full bg-indigo-600 px-3 py-1 text-xs font-medium text-white"
          >
            有効にする
          </button>
        </div>
      )}

      {buckets &&
        SECTIONS.map(({ key, label, emphasize }) => {
          const tasks = buckets[key];
          if (tasks.length === 0) return null;
          return (
            <section key={key} className="mt-4">
              <h2
                className={`px-4 py-1 text-sm font-semibold ${
                  emphasize ? "text-red-600" : "text-neutral-500"
                }`}
              >
                {label} ({tasks.length})
              </h2>
              <div className="mx-4 rounded-lg border border-neutral-200 bg-white">
                {tasks.map((task) => (
                  <TaskRow
                    key={task.id}
                    task={task}
                    course={task.course_id ? courseMap.get(task.course_id) : undefined}
                    onToggleDone={handleToggleDone}
                    overdue={key === "overdue"}
                  />
                ))}
              </div>
            </section>
          );
        })}

      {buckets && Object.values(buckets).every((tasks) => tasks.length === 0) && (
        <p className="mt-10 text-center text-sm text-neutral-400">
          タスクはまだありません。「貼り付け登録」から追加しましょう。
        </p>
      )}
    </div>
  );
}

export default function Home() {
  return (
    <RequireAuth>
      <HomeContent />
    </RequireAuth>
  );
}
