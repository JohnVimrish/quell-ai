import { useEffect } from "react";

const languageOptions = [
  { value: "en", label: "English" },
  { value: "es", label: "Spanish" },
  { value: "fr", label: "French" },
  { value: "de", label: "German" },
  { value: "zh", label: "Chinese" },
  { value: "auto", label: "Auto detect" },
];

export default function MessageUnderstandingDemo() {
  useEffect(() => {
    const previousTitle = document.title;
    document.title = "Message Lab";
    return () => {
      document.title = previousTitle;
    };
  }, []);

  return (
    <div className="section-padding">
      <div className="glass-panel" style={{ padding: "32px", marginBottom: "24px" }}>
        <h1 className="page-title">Message Lab</h1>
        <p className="page-intro">This lab is being rebuilt. The UI shell and styling are retained; interactive features are temporarily disabled.</p>
      </div>

      <div className="labs-layout">
        <div className="labs-pane labs-pane-input">
          <form onSubmit={(e) => e.preventDefault()} className="labs-card" style={{ display: "grid", gap: "16px" }}>
            <div className="labs-row">
              <label className="labs-label">
                Sender language
                <select className="labs-select" defaultValue="auto" disabled>
                  {languageOptions.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </label>
              <label className="labs-label">
                Your language
                <select className="labs-select" defaultValue="en" disabled>
                  {languageOptions.slice(0, 5).map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </label>
            </div>

            <label className="labs-label">
              Message text
              <textarea className="labs-textarea" rows={6} placeholder="Paste a long or multilingual message..." disabled />
            </label>

            <div className="labs-row labs-row-stack">
              <label className="labs-label">
                Image (optional)
                <input type="file" accept="image/*" className="labs-file-input" disabled />
              </label>
              <label className="labs-label">
                or Image URL
                <input type="url" placeholder="https://example.com/image.jpg" className="labs-input" disabled />
              </label>
            </div>

            <p className="labs-error" style={{ margin: 0 }}>Features are temporarily disabled.</p>

            <div className="labs-button-row">
              <button type="submit" className="button-engage" disabled>Send Message</button>
              <button type="button" className="button-outline" disabled>Describe Image</button>
            </div>
          </form>
        </div>

        <div className="labs-pane labs-pane-output">
          <div className="labs-empty-state">
            <h2>Temporarily unavailable</h2>
            <p>We’re rebuilding Message Lab. The styles are intact so you can continue design work.</p>
          </div>
        </div>
      </div>
    </div>
  );
}

