"use client";

import Link from "next/link";

import { formatDueAt } from "@/lib/format";
import type { Course, Task } from "@/lib/types";
import { TASK_TYPE_LABEL } from "@/lib/types";

export function TaskRow({
  task,
  course,
  onToggleDone,
  overdue = false,
}: {
  task: Task;
  course: Course | undefined;
  onToggleDone: (task: Task) => void;
  overdue?: boolean;
}) {
  return (
    <div className="flex items-center gap-3 border-b border-neutral-100 px-4 py-3 last:border-b-0">
      <input
        type="checkbox"
        checked={task.status === "done"}
        onChange={() => onToggleDone(task)}
        className="h-5 w-5 shrink-0 accent-indigo-600"
        aria-label="完了にする"
      />
      <Link href={`/tasks/${task.id}`} className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          {course && (
            <span
              className="h-2 w-2 shrink-0 rounded-full"
              style={{ backgroundColor: course.color }}
            />
          )}
          <span className="truncate text-sm font-medium text-neutral-900">{task.title}</span>
        </div>
        <div className="mt-0.5 flex items-center gap-2 text-xs text-neutral-500">
          {course && <span>{course.name}</span>}
          <span className="rounded bg-neutral-100 px-1.5 py-0.5">{TASK_TYPE_LABEL[task.type]}</span>
          <span className={overdue ? "font-semibold text-red-600" : ""}>{formatDueAt(task.due_at)}</span>
        </div>
      </Link>
    </div>
  );
}
