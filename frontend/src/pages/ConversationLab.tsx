import { useState } from "react";
import "./ConversationLab.css";

const HERO_METRICS = [
  { label: "Avg response", value: "02:17" },
  { label: "Context recall", value: "98%" },
  { label: "Voice confidence", value: "4.8/5" },
  { label: "Meetings covered", value: "126" },
];

const PROMPT_IDEAS = [
  "Create a meeting recap in my voice",
  "Draft a response for the client update",
  "Summarize the RFP thread",
  "Translate the voice note to English",
];

const FEATURE_CARDS = [
  {
    title: "Realtime Collaboration",
    body: "Route live audio or chat requests into the lab environment. The assistant keeps up with nuance and mirrors your tone.",
  },
  {
    title: "Voice + Text Modes",
    body: "Switch between generated audio answers and concise text summaries. Each mode inherits your access controls.",
  },
  {
    title: "Model Memory",
    body: "Every interaction is staged and can be approved before being published to your system of record.",
  },
];

type ChatMessage = { id: string; role: "ai" | "user"; text: string };

export default function ConversationLab() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "m-1",
      role: "ai",
      text:
        "Welcome back. I can join meetings, synthesize context, or produce a quick voice draft. What should we explore?",
    },
  ]);
  const [draft, setDraft] = useState("");

  const handleSend = () => {
    const trimmed = draft.trim();
    if (!trimmed) return;
    setMessages((prev) => [
      ...prev,
      { id: `u-${Date.now()}`, role: "user", text: trimmed },
      {
        id: `a-${Date.now() + 1}`,
        role: "ai",
        text:
          "(Demo reply) Got it. In the full experience this response is generated from your approved knowledge sources.",
      },
    ]);
    setDraft("");
  };

  return (
    <div className="lab-shell">
      <section className="lab-hero">
        <div className="lab-glass lab-hero-card">
          <div className="lab-chip-row">
            <span className="lab-chip">Proposal Mode</span>
            <span className="lab-chip">Live transcription</span>
            <span className="lab-chip">Voice synthesis</span>
          </div>
          <h1 className="page-title" style={{ margin: "4px 0 0" }}>
            Conversation Lab
          </h1>
          <p style={{ color: "var(--color-grey-700)", lineHeight: 1.7 }}>
            A focused surface for experimenting with Quell AI&apos;s conversational presence. The layout mirrors the
            original test-2 mock while staying aligned with the landing page system.
          </p>
          <div className="lab-metric-list">
            {HERO_METRICS.map((metric) => (
              <div key={metric.label} className="lab-metric">
                <span>{metric.label}</span>
                <span>{metric.value}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="lab-glass lab-hero-card">
          <h2 style={{ margin: 0, fontSize: "1.4rem" }}>What you can try</h2>
          <p style={{ color: "var(--color-grey-700)", marginBottom: 12 }}>
            Use the conversation surface or launch a voice run. Every test remains in this lab until you promote it.
          </p>
          <div className="lab-prompts">
            {PROMPT_IDEAS.map((prompt) => (
              <span key={prompt} className="lab-prompt">
                {prompt}
              </span>
            ))}
          </div>
          <div style={{ marginTop: 16, display: "grid", gap: 8 }}>
            <button
              type="button"
              className="button-engage"
              style={{ justifyContent: "center" }}
              onClick={handleSend}
            >
              Run sample prompt
            </button>
            <small style={{ color: "var(--color-grey-600)" }}>
              * This demo reuses landing-page tokens for buttons, inputs, and glassmorphism.
            </small>
          </div>
        </div>
      </section>

      <section className="lab-grid">
        {FEATURE_CARDS.map((card) => (
          <div key={card.title} className="lab-glass lab-grid-card">
            <h3>{card.title}</h3>
            <p>{card.body}</p>
          </div>
        ))}
      </section>

      <section className="lab-chat">
        <div className="lab-glass lab-chat-panel">
          <div className="lab-chat-messages">
            {messages.map((message) => (
              <div key={message.id} className="lab-chat-row">
                <div className={`lab-avatar ${message.role === "user" ? "user" : ""}`} aria-hidden />
                <div className="lab-bubble">
                  <p style={{ margin: 0 }}>{message.text}</p>
                </div>
              </div>
            ))}
          </div>
          <div className="lab-chat-input">
            <input
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  event.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Type your message or ask Quell AI anything..."
            />
            <button type="button" className="button-engage" onClick={handleSend}>
              Send
            </button>
          </div>
        </div>

        <div className="lab-glass lab-audio-card">
          <div className="lab-audio-meta">
            <div className="lab-audio-thumb" aria-hidden />
            <div>
              <div style={{ fontWeight: 700 }}>Voice draft</div>
              <div style={{ color: "var(--color-grey-600)", fontSize: "0.9rem" }}>Synthesized tone: Calm Analyst</div>
            </div>
          </div>
          <div className="lab-progress">
            <span style={{ width: "58%" }} />
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", color: "var(--color-grey-600)", fontSize: "0.85rem" }}>
            <span>01:12</span>
            <span>02:05</span>
          </div>
          <p style={{ margin: 0, color: "var(--color-grey-700)" }}>
            Preview how Quell AI would present your status update in a short audio clip before sending it to the team.
          </p>
          <div style={{ display: "flex", gap: 12 }}>
            <button type="button" className="button-engage" style={{ flex: 1 }}>
              Play
            </button>
            <button type="button" className="button-outline" style={{ flex: 1 }}>
              Download
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}

