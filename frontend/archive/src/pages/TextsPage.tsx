export default function TextsPage() {
  return (
    <div className="section-padding">
      <div className="glass-panel" style={{ padding: "48px" }}>
        <h1 style={{ fontSize: "clamp(2.5rem, 4vw, 3rem)", marginBottom: "16px" }}>Messages & Channels</h1>
        <p style={{ color: "var(--color-grey-600)", fontSize: "1.15rem", lineHeight: 1.7 }}>
          The assistant monitors Slack and Teams mentions while respecting your VIP whitelist. Configure tone mirroring, escalation paths, and sentiment alerts straight from here.
        </p>
      </div>

      <div className="glass-panel" style={{ padding: "32px", marginTop: "24px" }}>
        <h2 style={{ marginTop: 0, color: "var(--color-grey-900)" }}>Coming up next</h2>
        <ul className="bullet-list">
          <li>Thread-aware summaries that recap Slack channels alongside call transcripts.</li>
          <li>Per-channel presence rules, so the AI only replies when your status is set away.</li>
          <li>Escalation workflows that promote unresolved chats to scheduled follow-up calls.</li>
        </ul>
      </div>
    </div>
  );
}


