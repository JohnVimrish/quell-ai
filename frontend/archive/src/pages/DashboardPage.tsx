import { useEffect, useState } from "react";

type MetricState = {
  callsHandled: number;
  meetingsCovered: number;
  messagesReplied: number;
};

const initialMetrics: MetricState = {
  callsHandled: 0,
  meetingsCovered: 0,
  messagesReplied: 0,
};

export default function DashboardPage() {
  const [metrics, setMetrics] = useState(initialMetrics);

  useEffect(() => {
    let isMounted = true;
    async function loadMetrics() {
      try {
        const [callsRes, meetingsRes, messagesRes] = await Promise.all([
          fetch("/api/calls?page=1&limit=5", { credentials: "include" }),
          fetch("/api/meetings?page=1&limit=5", { credentials: "include" }),
          fetch("/api/texts/conversations?page=1&limit=5", { credentials: "include" }),
        ]);

        if (!isMounted) return;

        const callsJson = callsRes.ok ? await callsRes.json() : { pagination: { total: 0 } };
        const meetingsJson = meetingsRes.ok ? await meetingsRes.json() : { pagination: { total: 0 } };
        const messagesJson = messagesRes.ok ? await messagesRes.json() : { pagination: { total: 0 } };

        setMetrics({
          callsHandled: callsJson.pagination?.total ?? 0,
          meetingsCovered: meetingsJson.pagination?.total ?? 0,
          messagesReplied: messagesJson.pagination?.total ?? 0,
        });
      } catch {
        if (!isMounted) return;
        setMetrics(initialMetrics);
      }
    }

    loadMetrics();
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="dashboard-page section-padding">
      <div className="glass-panel" style={{ padding: "60px" }}>
        <header style={{ marginBottom: "48px" }}>
          <h1
            style={{
              margin: 0,
              fontSize: "clamp(2.5rem, 5vw, 3.5rem)",
              fontWeight: 800,
              background: "var(--gradient-orange-green)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              backgroundClip: "text",
              letterSpacing: "-0.04em",
            }}
          >
            Communication pulse
          </h1>
          <p
            style={{
              marginTop: "20px",
              color: "var(--color-grey-600)",
              lineHeight: 1.8,
              fontSize: "1.15rem",
              maxWidth: "720px",
            }}
          >
            Calls, meetings, and messages now flow through a single assistant. This dashboard keeps the highlights close: AI coverage, open action items, and document shares that need review.
          </p>
        </header>

        <section className="placeholder-cards">
          <article className="placeholder-card" aria-label="Call coverage">
            <h3>Calls delegated</h3>
            <p>The assistant handled <strong>{metrics.callsHandled}</strong> calls in the recent window, escalating only VIP or sensitive requests.</p>
          </article>
          <article className="placeholder-card" aria-label="Meeting coverage">
            <h3>Meetings covered</h3>
            <p><strong>{metrics.meetingsCovered}</strong> sessions captured with transcripts, summaries, and sentiment scores ready for review.</p>
          </article>
          <article className="placeholder-card" aria-label="Messages coverage">
            <h3>Messages answered</h3>
            <p><strong>{metrics.messagesReplied}</strong> conversations auto-responded with your tone, while important contacts ping you directly.</p>
          </article>
        </section>

        <section className="placeholder-cards" style={{ marginTop: "32px" }}>
          <article className="placeholder-card" aria-label="Upcoming">
            <h3>Upcoming handoffs</h3>
            <p>Review the next AI-led Zoom or Teams meetings, confirm agenda documents, and trigger voice clone warm-ups.</p>
          </article>
          <article className="placeholder-card" aria-label="Document policy">
            <h3>Document policy health</h3>
            <p>Keep an eye on which decks are shareable, who viewed them, and when retention timers will clean the archive.</p>
          </article>
          <article className="placeholder-card" aria-label="Insights">
            <h3>Insights and feedback</h3>
            <p>Capture reviewer feedback on AI performance and feed new instructions to tighten the next interaction.</p>
          </article>
        </section>
      </div>
    </div>
  );
}
