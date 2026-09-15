"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useAuth } from "@/lib/auth";

const LINKS = [
  { href: "/", label: "ホーム" },
  { href: "/paste", label: "貼り付け登録" },
  { href: "/courses", label: "科目" },
];

export function NavBar() {
  const pathname = usePathname();
  const { isSignedIn } = useAuth();

  if (!isSignedIn || pathname === "/login") return null;

  return (
    <nav className="sticky bottom-0 z-10 flex border-t border-neutral-200 bg-white sm:sticky sm:top-0 sm:border-b sm:border-t-0">
      {LINKS.map((link) => {
        const active = pathname === link.href;
        return (
          <Link
            key={link.href}
            href={link.href}
            className={`flex-1 py-3 text-center text-sm font-medium ${
              active ? "text-indigo-600" : "text-neutral-500"
            }`}
          >
            {link.label}
          </Link>
        );
      })}
    </nav>
  );
}
