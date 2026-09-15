"use client";

import { useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { useAuth } from "@/lib/auth";

export function RequireAuth({ children }: { children: ReactNode }) {
  const { isSignedIn, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isSignedIn) {
      router.replace("/login");
    }
  }, [isLoading, isSignedIn, router]);

  if (isLoading || !isSignedIn) {
    return <div className="p-6 text-sm text-neutral-500">読み込み中...</div>;
  }

  return <>{children}</>;
}
