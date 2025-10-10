import { useState } from "react";

export default function ContactsPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [showAddModal, setShowAddModal] = useState(false);

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
          Contact Management
        </h1>
        <p style={{ color: "var(--color-grey-600)", fontSize: "1.15rem", margin: 0 }}>
          Maintain whitelists, block lists, and keep every conversation route under your control.
        </p>
      </div>

      <div className="glass-panel" style={{ padding: "40px" }}>
        {/* Header Actions */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "32px", flexWrap: "wrap", gap: "16px" }}>
          <div style={{ flex: "1 1 300px" }}>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search contacts..."
              style={{
                width: "100%",
                padding: "12px 16px",
                border: "2px solid var(--color-grey-300)",
                borderRadius: "var(--radius-full)",
                fontSize: "1rem"
              }}
            />
          </div>

          <div style={{ display: "flex", gap: "12px" }}>
            <button 
              className="button-primary"
              onClick={() => setShowAddModal(true)}
            >
              <i className="fas fa-plus"></i> Add Contact
            </button>
            <button className="button-outline">
              <i className="fas fa-upload"></i> Import
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="placeholder-cards" style={{ marginBottom: "32px" }}>
          <div className="placeholder-card">
            <h3>Total Contacts</h3>
            <p style={{ fontSize: "2rem", fontWeight: 800, margin: "12px 0", color: "var(--color-grey-900)" }}>
              523
            </p>
          </div>

          <div className="placeholder-card">
            <h3>Whitelisted</h3>
            <p style={{ fontSize: "2rem", fontWeight: 800, margin: "12px 0", color: "var(--color-grey-900)" }}>
              87
            </p>
          </div>

          <div className="placeholder-card">
            <h3>Blocked</h3>
            <p style={{ fontSize: "2rem", fontWeight: 800, margin: "12px 0", color: "var(--color-grey-900)" }}>
              23
            </p>
          </div>

          <div className="placeholder-card">
            <h3>Active (30d)</h3>
            <p style={{ fontSize: "2rem", fontWeight: 800, margin: "12px 0", color: "var(--color-grey-900)" }}>
              156
            </p>
          </div>
        </div>

        {/* Contact List Placeholder */}
        <div style={{ 
          textAlign: "center", 
          padding: "60px",
          background: "var(--color-grey-50)",
          borderRadius: "var(--radius-large)",
          color: "var(--color-grey-600)"
        }}>
          <i className="fas fa-address-book" style={{ fontSize: "3rem", marginBottom: "16px", opacity: 0.3 }}></i>
          <p>Your contacts will appear here. Click "Add Contact" to get started.</p>
        </div>
      </div>

      {/* Add Contact Modal */}
      {showAddModal && (
        <div className="auth-page" style={{
          position: "fixed",
          inset: 0,
          background: "rgba(0, 0, 0, 0.5)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 1000
        }}>
          <div className="glass-panel" style={{ 
            maxWidth: "500px", 
            width: "90%", 
            padding: "40px",
            position: "relative"
          }}>
            <button 
              onClick={() => setShowAddModal(false)}
              style={{
                position: "absolute",
                top: "20px",
                right: "20px",
                background: "none",
                border: "none",
                fontSize: "1.5rem",
                cursor: "pointer",
                color: "var(--color-grey-600)"
              }}
            >
              ×
            </button>
            
            <h2 style={{ marginBottom: "24px", color: "var(--color-grey-900)" }}>Add New Contact</h2>
            
            <form className="auth-form">
              <div className="form-group">
                <label>Name</label>
                <input type="text" placeholder="John Doe" required />
              </div>

              <div className="form-group">
                <label>Phone Number</label>
                <input type="tel" placeholder="+1234567890" required />
              </div>

              <div className="form-group">
                <label>Email</label>
                <input type="email" placeholder="john@example.com" />
              </div>

              <div style={{ display: "flex", gap: "12px", marginTop: "24px" }}>
                <button type="button" className="button-outline" onClick={() => setShowAddModal(false)} style={{ flex: 1 }}>
                  Cancel
                </button>
                <button type="submit" className="button-primary" style={{ flex: 1 }}>
                  Save Contact
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}


