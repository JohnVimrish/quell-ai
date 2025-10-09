import { useState } from "react";

export default function SettingsPage() {
  const [aiEnabled, setAiEnabled] = useState(true);
  const [notifications, setNotifications] = useState(true);

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
          Settings
        </h1>
        <p style={{ color: "var(--color-grey-600)", fontSize: "1.15rem", margin: 0 }}>
          Configure your AI copilot preferences and communication settings.
        </p>
      </div>

      <div className="glass-panel" style={{ padding: "40px" }}>
        <div style={{ display: "grid", gap: "32px", maxWidth: "800px" }}>
          {/* AI Copilot Settings */}
          <div>
            <h3 style={{ marginBottom: "20px", color: "var(--color-grey-900)" }}>
              <i className="fas fa-robot"></i> AI Copilot
            </h3>
            <div className="placeholder-card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <h4 style={{ margin: "0 0 8px", color: "var(--color-grey-900)" }}>Enable AI Assistant</h4>
                  <p style={{ margin: 0, color: "var(--color-grey-600)", fontSize: "0.95rem" }}>
                    Let AI handle incoming calls and messages automatically
                  </p>
                </div>
                <label style={{ position: "relative", display: "inline-block", width: "60px", height: "34px" }}>
                  <input
                    type="checkbox"
                    checked={aiEnabled}
                    onChange={(e) => setAiEnabled(e.target.checked)}
                    style={{ opacity: 0, width: 0, height: 0 }}
                  />
                  <span style={{
                    position: "absolute",
                    cursor: "pointer",
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    background: aiEnabled ? "var(--color-green-500)" : "var(--color-grey-300)",
                    transition: "0.4s",
                    borderRadius: "34px"
                  }}>
                    <span style={{
                      position: "absolute",
                      content: '""',
                      height: "26px",
                      width: "26px",
                      left: aiEnabled ? "30px" : "4px",
                      bottom: "4px",
                      background: "white",
                      transition: "0.4s",
                      borderRadius: "50%"
                    }} />
                  </span>
                </label>
              </div>
            </div>
          </div>

          {/* Notification Settings */}
          <div>
            <h3 style={{ marginBottom: "20px", color: "var(--color-grey-900)" }}>
              <i className="fas fa-bell"></i> Notifications
            </h3>
            <div className="placeholder-card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <h4 style={{ margin: "0 0 8px", color: "var(--color-grey-900)" }}>Push Notifications</h4>
                  <p style={{ margin: 0, color: "var(--color-grey-600)", fontSize: "0.95rem" }}>
                    Receive notifications for important calls and messages
                  </p>
                </div>
                <label style={{ position: "relative", display: "inline-block", width: "60px", height: "34px" }}>
                  <input
                    type="checkbox"
                    checked={notifications}
                    onChange={(e) => setNotifications(e.target.checked)}
                    style={{ opacity: 0, width: 0, height: 0 }}
                  />
                  <span style={{
                    position: "absolute",
                    cursor: "pointer",
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    background: notifications ? "var(--color-orange-500)" : "var(--color-grey-300)",
                    transition: "0.4s",
                    borderRadius: "34px"
                  }}>
                    <span style={{
                      position: "absolute",
                      content: '""',
                      height: "26px",
                      width: "26px",
                      left: notifications ? "30px" : "4px",
                      bottom: "4px",
                      background: "white",
                      transition: "0.4s",
                      borderRadius: "50%"
                    }} />
                  </span>
                </label>
              </div>
            </div>
          </div>

          {/* Account Section */}
          <div>
            <h3 style={{ marginBottom: "20px", color: "var(--color-grey-900)" }}>
              <i className="fas fa-user"></i> Account
            </h3>
            <div className="placeholder-cards">
              <button className="placeholder-card" style={{ cursor: "pointer", textAlign: "left", width: "100%" }}>
                <h4 style={{ margin: "0 0 8px" }}>Profile Settings</h4>
                <p style={{ margin: 0, fontSize: "0.9rem" }}>Update your personal information</p>
              </button>

              <button className="placeholder-card" style={{ cursor: "pointer", textAlign: "left", width: "100%" }}>
                <h4 style={{ margin: "0 0 8px" }}>Security</h4>
                <p style={{ margin: 0, fontSize: "0.9rem" }}>Change password and 2FA settings</p>
              </button>

              <button className="placeholder-card" style={{ cursor: "pointer", textAlign: "left", width: "100%" }}>
                <h4 style={{ margin: "0 0 8px" }}>Billing</h4>
                <p style={{ margin: 0, fontSize: "0.9rem" }}>Manage subscription and payments</p>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

