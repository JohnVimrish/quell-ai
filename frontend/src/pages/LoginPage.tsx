import { useState } from "react";
import { useAuth } from "../components/AuthProvider";

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: Implement actual login logic
    console.log("Login attempt:", { email, password });
    login();
  };

  return (
    <div className="auth-page section-padding">
      <div className="auth-container">
        <div className="auth-card glass-panel">
          <h1 style={{ 
            fontSize: "2.5rem", 
            fontWeight: 800, 
            marginBottom: "12px",
            color: "var(--color-grey-900)"
          }}>
            Welcome Back
          </h1>
          <p style={{ 
            color: "var(--color-grey-600)", 
            marginBottom: "32px",
            fontSize: "1.1rem"
          }}>
            Sign in to your account to continue
          </p>

          <form onSubmit={handleSubmit} className="auth-form">
            <div className="form-group">
              <label htmlFor="email">Email Address</label>
              <input
                type="email"
                id="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input
                type="password"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="********"
                required
              />
            </div>

            <button type="submit" className="button-primary" style={{ width: "100%" }}>
              Sign In
            </button>
          </form>

          <div className="auth-footer">
            <p>
              Don't have an account?{" "}
              <a href="/legacy/signup.html" style={{ color: "var(--color-orange-500)", fontWeight: 600 }}>
                Sign up
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}


