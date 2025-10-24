export default function LabsPlayground() {
  return (
    <div className="section-padding">
      <div className="glass-panel" style={{ padding: "48px", marginBottom: "32px" }}>
        <h1 className="page-title">Labs Playground</h1>
        <p className="page-intro">
          This developer playground is being rebuilt. The UI shell and styling are retained; interactive features are
          temporarily disabled.
        </p>
      </div>

      <section className="glass-panel" style={{ padding: "28px", marginBottom: "28px" }}>
        <h2>Status</h2>
        <p style={{ color: "var(--color-grey-600)", marginBottom: "12px" }}>
          Feature suite temporarily unavailable while we refactor.
        </p>
        <form className="labs-row" onSubmit={(e) => e.preventDefault()}>
          <input className="input" placeholder="API key" disabled />
          <button className="button-engage" disabled>
            Save
          </button>
        </form>
      </section>

      <section className="glass-panel" style={{ padding: "28px", marginBottom: "28px" }}>
        <h2>Prompt Builder</h2>
        <div className="labs-grid" style={{ gap: "16px" }}>
          <textarea className="textarea" rows={4} placeholder="System instructions" disabled />
          <div className="labs-card" style={{ padding: "16px" }}>
            <div style={{ display: "grid", gap: "8px" }}>
              <input className="input" placeholder="Objective" disabled />
              <input className="input" placeholder="Constraints" disabled />
            </div>
          </div>
          <button className="button-engage" disabled>
            Generate
          </button>
        </div>
      </section>

      <section className="glass-panel" style={{ padding: "28px", marginBottom: "28px" }}>
        <h2>Chat</h2>
        <div className="labs-card" style={{ padding: "16px" }}>
          <div style={{ display: "flex", gap: "12px" }}>
            <input className="input" placeholder="Ask something..." disabled />
            <button className="button-engage" disabled>
              Send
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}

