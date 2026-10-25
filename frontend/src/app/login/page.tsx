"use client";

import { useAuth } from "@/lib/auth";

export default function LoginPage() {
  const { signIn } = useAuth();

  return (
    <div className="flex min-h-[80vh] flex-col items-center justify-center gap-6 p-6 text-center">
      <div>
        <h1 className="text-2xl font-bold text-indigo-600">TaskCampus</h1>
        <p className="mt-2 text-sm text-neutral-500">貼るだけ登録。入力ゼロのタスク管理。</p>
      </div>
      <button
        onClick={signIn}
        className="flex items-center gap-2 rounded-lg border border-neutral-300 bg-white px-6 py-3 text-sm font-medium shadow-sm hover:bg-neutral-50"
      >
        Googleでログイン
      </button>
    </div>
  );
}
