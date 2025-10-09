export default function ReportsPage() {
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
          Reports & Analytics
        </h1>
        <p style={{ color: "var(--color-grey-600)", fontSize: "1.15rem", margin: 0 }}>
          View detailed insights about your calls, messages, and AI performance.
        </p>
      </div>

      <div className="glass-panel" style={{ padding: "40px" }}>
        <div className="placeholder-cards">
          <div className="placeholder-card">
            <h3>Call Volume</h3>
            <div style={{ height: "200px", background: "var(--color-grey-50)", borderRadius: "var(--radius-medium)", display: "flex", alignItems: "center", justifyContent: "center", marginTop: "16px" }}>
              <span style={{ color: "var(--color-grey-400)" }}>Chart Placeholder</span>
            </div>
          </div>

          <div className="placeholder-card">
            <h3>AI Performance</h3>
            <div style={{ height: "200px", background: "var(--color-grey-50)", borderRadius: "var(--radius-medium)", display: "flex", alignItems: "center", justifyContent: "center", marginTop: "16px" }}>
              <span style={{ color: "var(--color-grey-400)" }}>Chart Placeholder</span>
            </div>
          </div>

          <div className="placeholder-card">
            <h3>Peak Hours</h3>
            <div style={{ height: "200px", background: "var(--color-grey-50)", borderRadius: "var(--radius-medium)", display: "flex", alignItems: "center", justifyContent: "center", marginTop: "16px" }}>
              <span style={{ color: "var(--color-grey-400)" }}>Chart Placeholder</span>
            </div>
          </div>

          <div className="placeholder-card">
            <h3>Response Times</h3>
            <div style={{ height: "200px", background: "var(--color-grey-50)", borderRadius: "var(--radius-medium)", display: "flex", alignItems: "center", justifyContent: "center", marginTop: "16px" }}>
              <span style={{ color: "var(--color-grey-400)" }}>Chart Placeholder</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

