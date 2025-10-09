import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function SignupPage() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (formData.password !== formData.confirmPassword) {
      alert("Passwords do not match!");
      return;
    }

    // TODO: Implement actual signup logic
    console.log("Signup attempt:", formData);
    navigate("/dashboard");
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
            Create Account
          </h1>
          <p style={{ 
            color: "var(--color-grey-600)", 
            marginBottom: "32px",
            fontSize: "1.1rem"
          }}>
            Join us to start your AI-powered journey
          </p>

          <form onSubmit={handleSubmit} className="auth-form">
            <div className="form-group">
              <label htmlFor="name">Full Name</label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleChange}
                placeholder="John Doe"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="email">Email Address</label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="you@example.com"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="••••••••"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="confirmPassword">Confirm Password</label>
              <input
                type="password"
                id="confirmPassword"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleChange}
                placeholder="••••••••"
                required
              />
            </div>

            <button type="submit" className="button-primary" style={{ width: "100%" }}>
              Create Account
            </button>
          </form>

          <div className="auth-footer">
            <p>
              Already have an account?{" "}
              <a href="/login" style={{ color: "var(--color-orange-500)", fontWeight: 600 }}>
                Sign in
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

