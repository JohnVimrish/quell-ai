export default function TextsPage() {
  return (
    <div className="section-padding">
      <div className="glass-panel" style={{ padding: "48px", marginBottom: "32px" }}>
        <h1 style={{
          fontSize: "clamp(2.5rem, 4vw, 3rem)",
          fontWeight: 800,
          margin: "0 0 16px",
          background: "var(--gradient-orange-green)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
          backgroundClip: "text"
        }}>
          Text Messages
        </h1>
        <p style={{ color: "var(--color-grey-600)", fontSize: "1.15rem", margin: 0 }}>
          Manage your text conversations and AI-powered responses.
        </p>
      </div>

      <div className="glass-panel" style={{ padding: "40px" }}>
        <div className="placeholder-cards">
          <div className="placeholder-card">
            <h3>Total Messages</h3>
            <p style={{ fontSize: "2rem", fontWeight: 800, margin: "12px 0", color: "var(--color-grey-900)" }}>
              1,234
            </p>
            <span style={{ color: "var(--color-green-600)", fontSize: "0.9rem" }}>↑ 18% this week</span>
          </div>

          <div className="placeholder-card">
            <h3>AI Responses</h3>
            <p style={{ fontSize: "2rem", fontWeight: 800, margin: "12px 0", color: "var(--color-grey-900)" }}>
              892
            </p>
            <span style={{ color: "var(--color-orange-600)", fontSize: "0.9rem" }}>↑ 25% this week</span>
          </div>

          <div className="placeholder-card">
            <h3>Spam Blocked</h3>
            <p style={{ fontSize: "2rem", fontWeight: 800, margin: "12px 0", color: "var(--color-grey-900)" }}>
              142
            </p>
            <span style={{ color: "var(--color-green-600)", fontSize: "0.9rem" }}>↓ 8% this week</span>
          </div>
        </div>

        <div style={{ 
          textAlign: "center", 
          padding: "60px",
          background: "var(--color-grey-50)",
          borderRadius: "var(--radius-large)",
          color: "var(--color-grey-600)",
          marginTop: "32px"
        }}>
          <i className="fas fa-sms" style={{ fontSize: "3rem", marginBottom: "16px", opacity: 0.3 }}></i>
          <p>Your text messages will appear here.</p>
        </div>
      </div>
    </div>
  );
}

