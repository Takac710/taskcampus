"use client";

/**
 * Stub session for the MVP. The requirements doc calls for Google login via
 * Supabase Auth (F-01), which needs a Supabase project the developer sets up
 * outside this repo. Until then, "signing in" just flips a localStorage flag
 * so the rest of the app (which screens are reachable, nav visibility) can be
 * built and tried end-to-end; swap `signIn` for the real Supabase OAuth call
 * later without touching callers of `useAuth`.
 */

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

const STORAGE_KEY = "taskcampus_signed_in";

interface AuthState {
  isSignedIn: boolean;
  isLoading: boolean;
  signIn: () => void;
  signOut: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isSignedIn, setIsSignedIn] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    try {
      setIsSignedIn(window.localStorage.getItem(STORAGE_KEY) === "1");
    } catch {
      // localStorage unavailable (e.g. private mode) -- stay signed out
    } finally {
      setIsLoading(false);
    }
  }, []);

  const signIn = () => {
    try {
      window.localStorage.setItem(STORAGE_KEY, "1");
    } catch {
      // ignore
    }
    setIsSignedIn(true);
  };

  const signOut = () => {
    try {
      window.localStorage.removeItem(STORAGE_KEY);
    } catch {
      // ignore
    }
    setIsSignedIn(false);
  };

  return (
    <AuthContext.Provider value={{ isSignedIn, isLoading, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
