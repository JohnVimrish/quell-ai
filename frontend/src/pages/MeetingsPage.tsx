import { useEffect, useMemo, useState } from "react";

type MeetingRecord = {
  id: number;
  subject?: string;
  status?: string;
  channel?: string;
  started_at?: string | null;
  ended_at?: string | null;
  ai_participated?: boolean;
  topics?: string[];
  action_items?: string[];
  summary_text?: string | null;
};

type MeetingResponse = {
  meetings: MeetingRecord[];
  pagination: { page: number; total: number };
};

const defaultState: MeetingResponse = {
  meetings: [],
  pagination: { page: 1, total: 0 },
};

export default function MeetingsPage() {
  const [data, setData] = useState<MeetingResponse>(defaultState);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function loadMeetings() {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch("/api/meetings?page=1&limit=20", {
          credentials: "include",
        });
        if (!response.ok) {
          throw new Error(`request failed: ${response.status}`);
        }
        const payload = (await response.json()) as MeetingResponse;
        if (isMounted) {
          setData(payload);
        }
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "unknown error");
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }
    loadMeetings();
    return () => {
      isMounted = false;
    };
  }, []);

  const aiCoverage = useMemo(() => {
    if (!data.meetings.length) return 0;
    const handled = data.meetings.filter((meeting) => meeting.ai_participated).length;
    return Math.round((handled / data.meetings.length) * 100);
  }, [data.meetings]);

  return (
    <div className="section-padding">
      <div className="glass-panel" style={{ padding: "48px", marginBottom: "32px" }}>
        <h1 className="page-title">Meetings & Delegation</h1>
        <p className="page-intro">
          Track where the AI assistant joined on your behalf, review summaries, and fine-tune delegation rules for Zoom and Teams.
        </p>
      </div>

      <div className="grid-two" style={{ gap: "24px" }}>
        <div className="glass-panel" style={{ padding: "32px" }}>
          <h2 className="panel-title">Weekly Impact</h2>
          {loading ? (
            <p>Loading weekly metrics…</p>
          ) : error ? (
            <p role="alert">Unable to load meetings: {error}</p>
          ) : (
            <div className="metrics-grid">
              <div className="metric-card">
                <span className="metric-label">Sessions captured</span>
                <span className="metric-value">{data.pagination.total}</span>
              </div>
              <div className="metric-card">
                <span className="metric-label">AI coverage</span>
                <span className="metric-value">{aiCoverage}%</span>
              </div>
              <div className="metric-card">
                <span className="metric-label">Channels</span>
                <span className="metric-value">
                  {Array.from(new Set(data.meetings.map((meeting) => meeting.channel || "zoom"))).join(", ") || "zoom"}
                </span>
              </div>
            </div>
          )}
        </div>

        <div className="glass-panel" style={{ padding: "32px" }}>
          <h2 className="panel-title">Delegation checklist</h2>
          <ul className="bullet-list">
            <li>Auto-join windows respect your out-of-office schedule.</li>
            <li>Voice clone reminders trigger before customer-facing sessions.</li>
            <li>Document policies gate sensitive decks before sharing.</li>
            <li>Attendees see a disclosure when the AI represents you.</li>
          </ul>
        </div>
      </div>

      <div className="glass-panel" style={{ padding: "32px", marginTop: "32px" }}>
        <div className="panel-header">
          <h2 className="panel-title">Recent meetings</h2>
          <span className="panel-subtitle">
            The assistant keeps transcripts, highlights, and action items synchronized across channels.
          </span>
        </div>
        {loading && <p>Loading meeting history…</p>}
        {!loading && error && <p role="alert">{error}</p>}
        {!loading && !error && data.meetings.length === 0 && (
          <p>No meetings captured yet. Connect Zoom or Teams and enable delegation to see sessions here.</p>
        )}
        {!loading && !error && data.meetings.length > 0 && (
          <div className="table" role="table">
            <div className="table-row table-header" role="row">
              <span role="columnheader">Title</span>
              <span role="columnheader">Status</span>
              <span role="columnheader">Channel</span>
              <span role="columnheader">AI delegate</span>
              <span role="columnheader">Summary</span>
            </div>
            {data.meetings.map((meeting) => (
              <div key={meeting.id} className="table-row" role="row">
                <span role="cell">{meeting.subject || "Untitled meeting"}</span>
                <span role="cell">{meeting.status || "completed"}</span>
                <span role="cell">{meeting.channel || "zoom"}</span>
                <span role="cell">{meeting.ai_participated ? "AI covered" : "User"}</span>
                <span role="cell" title={meeting.summary_text || undefined}>
                  {meeting.summary_text ? meeting.summary_text.slice(0, 140) : "Summary pending"}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
