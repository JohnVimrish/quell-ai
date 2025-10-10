export default function DashboardPage() {
  return (
    <div className="dashboard-page section-padding">
      <div className="glass-panel" style={{ padding: "60px" }}>
        <div style={{ marginBottom: "48px" }}>
          <h1 style={{ 
            margin: 0, 
            fontSize: "clamp(2.5rem, 5vw, 3.5rem)", 
            fontWeight: 800,
            background: "var(--gradient-orange-green)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            backgroundClip: "text",
            letterSpacing: "-0.04em"
          }}>
            Dashboard overview
          </h1>
          <p style={{ 
            marginTop: "20px", 
            color: "var(--color-grey-600)", 
            lineHeight: 1.8,
            fontSize: "1.15rem"
          }}>
            See calls handled by the copilot, recent transcripts, and follow-up actions—all within a minimal workspace.
          </p>
        </div>
        <div className="placeholder-cards">
          <div className="placeholder-card">
            <h3>Live Calls</h3>
            <p>Monitor ongoing conversations and intervene instantly when a VIP calls.</p>
          </div>
          <div className="placeholder-card">
            <h3>Summaries</h3>
            <p>AI-generated briefs captured seconds after each call ends.</p>
          </div>
          <div className="placeholder-card">
            <h3>Insights</h3>
            <p>Understand volume, sentiment, and response times with a single glance.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
