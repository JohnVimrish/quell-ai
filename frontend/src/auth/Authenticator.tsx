import React, { useState } from "react";
import { createPortal } from "react-dom";
import { useAuth } from "../components/AuthProvider";

export default function Authenticator({ onClose }: { onClose?: () => void }) {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      // Hook up to your real auth here; using context login for now
      await new Promise((r) => setTimeout(r, 500));
      login();
      onClose?.();
    } finally {
      setLoading(false);
    }
  };

  // Create a glass-styled modal aligned with base.html visuals
  const modal = (
    <div
      aria-modal
      role="dialog"
      className="auth-overlay"
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.35)",
        backdropFilter: "blur(6px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
      onClick={onClose}
    >
      <div
        className="glass-panel"
        style={{
          width: "min(92vw, 520px)",
          padding: "28px",
          borderRadius: "12px",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <h3
          className="font-serif"
          style={{
            fontSize: "1.5rem",
            margin: 0,
            color: "var(--color-dark-text)",
          }}
        >
          Log In
        </h3>
        <p style={{ color: "var(--color-light-text)", marginTop: 8 }}>
          Access your Quell AI account
        </p>
        <form onSubmit={handleSubmit} style={{ marginTop: 18 }}>
          <label style={{ display: "block", marginBottom: 12 }}>
            <span style={{ display: "block", fontWeight: 600, marginBottom: 6 }}>
              Email
            </span>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              style={{
                width: "100%",
                padding: "12px 14px",
                borderRadius: 8,
                border: "1px solid var(--color-border-grey)",
                background: "rgba(255,255,255,0.9)",
              }}
            />
          </label>
          <label style={{ display: "block", marginBottom: 16 }}>
            <span style={{ display: "block", fontWeight: 600, marginBottom: 6 }}>
              Password
            </span>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{
                width: "100%",
                padding: "12px 14px",
                borderRadius: 8,
                border: "1px solid var(--color-border-grey)",
                background: "rgba(255,255,255,0.9)",
              }}
            />
          </label>
          <div style={{ display: "flex", gap: 12, justifyContent: "flex-end" }}>
            <button
              type="button"
              onClick={onClose}
              className="nav-pill nav-3d"
              style={{ padding: "10px 18px" }}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-3d"
              disabled={loading}
              style={{
                padding: "10px 18px",
                borderRadius: 9999,
                border: "1px solid var(--color-primary-blue)",
                background: "linear-gradient(180deg, var(--color-primary-blue), var(--color-hover-blue))",
                color: "#fff",
                fontWeight: 700,
              }}
            >
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );

  return createPortal(modal, document.body);
}

