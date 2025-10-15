import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

type AuthContextValue = {
  isAuthed: boolean;
  isEngaged: boolean;
  engage: () => void;
  login: () => void;
  logout: () => void;
  backToAbout: () => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate();
  const location = useLocation();
  const [isAuthed, setIsAuthed] = useState<boolean>(() => {
    try {
      return localStorage.getItem("qa_authed") === "1";
    } catch {
      return false;
    }
  });
  const [isEngaged, setIsEngaged] = useState<boolean>(() => {
    try {
      if (localStorage.getItem("qa_authed") === "1") return true;
      return localStorage.getItem("qa_engaged") === "1";
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

  useEffect(() => {
    try {
      if (isEngaged) localStorage.setItem("qa_engaged", "1");
      else localStorage.removeItem("qa_engaged");
    } catch {}
  }, [isEngaged]);

  useEffect(() => {
    if (isAuthed && !isEngaged) {
      setIsEngaged(true);
    }
  }, [isAuthed, isEngaged]);

  useEffect(() => {
    const engagedRoutes = ["/why", "/dashboard", "/calls", "/contacts", "/texts", "/reports", "/settings", "/labs"];
    if (!isEngaged && engagedRoutes.some((route) => location.pathname.startsWith(route))) {
      setIsEngaged(true);
    }
    if (!isAuthed && location.pathname === "/" && isEngaged) {
      setIsEngaged(false);
    }
  }, [isAuthed, isEngaged, location.pathname]);

  const value = useMemo<AuthContextValue>(() => ({
    isAuthed,
    isEngaged,
    engage: () => {
      setIsEngaged((prev) => (prev ? prev : true));
      if (location.pathname !== "/why") {
        navigate("/why");
      }
    },
    login: () => {
      setIsAuthed(true);
      setIsEngaged(true);
      if (location.pathname !== "/dashboard") {
        navigate("/dashboard");
      }
    },
    logout: () => {
      setIsAuthed(false);
      setIsEngaged(false);
      if (location.pathname !== "/") {
        navigate("/");
      }
    },
    backToAbout: () => {
      setIsEngaged(false);
      if (location.pathname !== "/") {
        navigate("/");
      }
    },
  }), [isAuthed, isEngaged, navigate, location.pathname]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}



