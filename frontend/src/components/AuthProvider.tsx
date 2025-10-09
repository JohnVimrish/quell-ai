import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

type AuthContextValue = {
  isAuthed: boolean;
  experience: () => void; // simulate logged-in UX
  login: () => void;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate();
  const [isAuthed, setIsAuthed] = useState<boolean>(() => {
    try {
      return localStorage.getItem("qa_authed") === "1";
    } catch {
      return false;
    }
  });

  useEffect(() => {
    try {
      if (isAuthed) localStorage.setItem("qa_authed", "1");
      else localStorage.removeItem("qa_authed");
    } catch {}
  }, [isAuthed]);

  const value = useMemo<AuthContextValue>(() => ({
    isAuthed,
    experience: () => {
      setIsAuthed(true);
      navigate("/dashboard");
    },
    login: () => {
      setIsAuthed(true);
      navigate("/dashboard");
    },
    logout: () => {
      setIsAuthed(false);
      navigate("/");
    },
  }), [isAuthed, navigate]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}


