import type {
  Course,
  DeadlineBuckets,
  ExtractedFields,
  ExtractResponse,
  Task,
  TaskType,
} from "./types";
import { supabase } from "./supabaseClient";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;

  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`API ${path} failed (${res.status}): ${body}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string }>("/health"),

  listCourses: (includeArchived = false) =>
    request<Course[]>(`/courses?include_archived=${includeArchived}`),
  createCourse: (data: { name: string; color: string }) =>
    request<Course>("/courses", { method: "POST", body: JSON.stringify(data) }),
  updateCourse: (id: string, data: Partial<{ name: string; color: string; archived: boolean }>) =>
    request<Course>(`/courses/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteCourse: (id: string) => request<void>(`/courses/${id}`, { method: "DELETE" }),

  listTasks: () => request<Task[]>("/tasks"),
  getTask: (id: string) => request<Task>(`/tasks/${id}`),
  createTask: (data: {
    title: string;
    course_id: string | null;
    type: TaskType;
    due_at: string | null;
    memo: string;
  }) => request<Task>("/tasks", { method: "POST", body: JSON.stringify(data) }),
  updateTask: (
    id: string,
    data: Partial<{
      title: string;
      course_id: string | null;
      type: TaskType;
      due_at: string | null;
      memo: string;
      status: "open" | "done";
    }>
  ) => request<Task>(`/tasks/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteTask: (id: string) => request<void>(`/tasks/${id}`, { method: "DELETE" }),
  deadlineBuckets: () => request<DeadlineBuckets>("/tasks/views/deadline-buckets"),

  vapidPublicKey: () => request<{ public_key: string }>("/push/vapid-public-key"),
  subscribePush: (subscription: PushSubscriptionJSON) =>
    request<{ status: string }>("/push/subscriptions", {
      method: "POST",
      body: JSON.stringify(subscription),
    }),

  extract: (rawText: string) =>
    request<ExtractResponse>("/extract", { method: "POST", body: JSON.stringify({ raw_text: rawText }) }),
  confirmExtraction: (extractionLogId: string, fields: ExtractedFields) =>
    request<Task>("/extract/confirm", {
      method: "POST",
      body: JSON.stringify({ extraction_log_id: extractionLogId, fields }),
    }),
};
