import { useState, useEffect } from "react";
 
interface Call {
  id: string;
  number: string;
  type: "incoming" | "outgoing" | "missed";
  status: string;
  duration: number;
  timestamp: string;
  ai_handled: boolean;
}

export default function CallsPage() {
  const [calls] = useState<Call[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    // TODO: Fetch calls from API
    setLoading(false);
  }, []);

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
          Call Management
        </h1>
        <p style={{ color: "var(--color-grey-600)", fontSize: "1.15rem", margin: 0 }}>
          Review every conversation Quell-AI handles, from spam blocks to VIP escalations.
        </p>
      </div>

      <div className="glass-panel" style={{ padding: "40px" }}>
        {/* Search and Filters */}
        <div style={{ marginBottom: "32px" }}>
          <div style={{ display: "flex", gap: "16px", flexWrap: "wrap" }}>
            <div style={{ flex: "1 1 300px" }}>
              <label style={{ 
                display: "block", 
                marginBottom: "8px", 
                fontWeight: 600,
                color: "var(--color-grey-700)"
              }}>
                Search Calls
              </label>
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search by number or name..."
                className="form-group input"
                style={{
                  width: "100%",
                  padding: "12px 16px",
                  border: "2px solid var(--color-grey-300)",
                  borderRadius: "var(--radius-medium)",
                  fontSize: "1rem"
                }}
              />
            </div>

            <div style={{ flex: "1 1 200px" }}>
              <label style={{ 
                display: "block", 
                marginBottom: "8px", 
                fontWeight: 600,
                color: "var(--color-grey-700)"
              }}>
                Filter
              </label>
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                style={{
                  width: "100%",
                  padding: "12px 16px",
                  border: "2px solid var(--color-grey-300)",
                  borderRadius: "var(--radius-medium)",
                  fontSize: "1rem",
                  fontFamily: "Arial, Helvetica, sans-serif"
                }}
              >
                <option value="all">All Calls</option>
                <option value="incoming">Incoming</option>
                <option value="outgoing">Outgoing</option>
                <option value="missed">Missed</option>
                <option value="spam">Spam</option>
                <option value="ai-handled">AI Handled</option>
              </select>
            </div>

            <div style={{ display: "flex", alignItems: "flex-end", gap: "12px" }}>
              <button className="button-primary">
                <i className="fas fa-sync-alt"></i> Refresh
              </button>
              <button className="button-outline">
                <i className="fas fa-download"></i> Export
              </button>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="placeholder-cards" style={{ marginBottom: "32px" }}>
          <div className="placeholder-card">
            <h3>Total Calls</h3>
            <p style={{ fontSize: "2rem", fontWeight: 800, margin: "12px 0", color: "var(--color-grey-900)" }}>
              247
            </p>
            <span style={{ color: "var(--color-green-600)", fontSize: "0.9rem" }}>↑ 15% this week</span>
          </div>

          <div className="placeholder-card">
            <h3>Answered</h3>
            <p style={{ fontSize: "2rem", fontWeight: 800, margin: "12px 0", color: "var(--color-grey-900)" }}>
              189
            </p>
            <span style={{ color: "var(--color-green-600)", fontSize: "0.9rem" }}>↑ 8% this week</span>
          </div>

          <div className="placeholder-card">
            <h3>AI Handled</h3>
            <p style={{ fontSize: "2rem", fontWeight: 800, margin: "12px 0", color: "var(--color-grey-900)" }}>
              156
            </p>
            <span style={{ color: "var(--color-orange-600)", fontSize: "0.9rem" }}>↑ 22% this week</span>
          </div>

          <div className="placeholder-card">
            <h3>Spam Blocked</h3>
            <p style={{ fontSize: "2rem", fontWeight: 800, margin: "12px 0", color: "var(--color-grey-900)" }}>
              58
            </p>
            <span style={{ color: "var(--color-green-600)", fontSize: "0.9rem" }}>↓ 12% this week</span>
          </div>
        </div>

        {/* Call List */}
        <div>
          <h3 style={{ marginBottom: "20px", color: "var(--color-grey-900)" }}>Recent Calls</h3>
          
          {loading ? (
            <div style={{ textAlign: "center", padding: "40px", color: "var(--color-grey-500)" }}>
              Loading calls...
            </div>
          ) : calls.length === 0 ? (
            <div style={{ 
              textAlign: "center", 
              padding: "60px",
              background: "var(--color-grey-50)",
              borderRadius: "var(--radius-large)",
              color: "var(--color-grey-600)"
            }}>
              <i className="fas fa-phone" style={{ fontSize: "3rem", marginBottom: "16px", opacity: 0.3 }}></i>
              <p>No calls found. Your call history will appear here.</p>
            </div>
          ) : (
            <div style={{ display: "grid", gap: "12px" }}>
              {/* Call items would go here */}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
