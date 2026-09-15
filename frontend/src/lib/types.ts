export type TaskType = "report" | "quiz" | "presentation" | "other";
export type TaskStatus = "open" | "done";
export type TaskSource = "manual" | "paste";

export const TASK_TYPE_LABEL: Record<TaskType, string> = {
  report: "レポート",
  quiz: "小テスト",
  presentation: "発表",
  other: "その他",
};

export interface Course {
  id: string;
  name: string;
  color: string;
  archived: boolean;
}

export interface Task {
  id: string;
  title: string;
  course_id: string | null;
  type: TaskType;
  due_at: string | null;
  memo: string;
  status: TaskStatus;
  source: TaskSource;
  created_at: string;
}

export interface ExtractedFields {
  course_id: string | null;
  course_name_guess: string | null;
  course_confidence: number;
  title: string;
  due_at: string | null;
  due_text_matched: string | null;
  type: TaskType;
}

export interface ExtractResponse {
  extraction_log_id: string;
  fields: ExtractedFields;
}

export interface DeadlineBuckets {
  overdue: Task[];
  today: Task[];
  this_week: Task[];
  later: Task[];
  no_due_date: Task[];
}
