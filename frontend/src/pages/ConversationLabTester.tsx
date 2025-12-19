import { useEffect, useRef, useState } from "react";

type SessionInfo = {
  sessionId: string;
  assistantName?: string;
  greeting?: string;
};

type UploadJob = {
  jobId: number;
  filename: string;
  status: string;
  summary?: string;
};

export default function ConversationLabTester() {
  const [session, setSession] = useState<SessionInfo | null>(null);
  const [status, setStatus] = useState<string>("");
  const [jobs, setJobs] = useState<UploadJob[]>([]);
  const [chatPrompt, setChatPrompt] = useState("What do you know about Alice?");
  const [chatReply, setChatReply] = useState<string>("");
  const pollRef = useRef<number | undefined>(undefined);

  useEffect(() => {
    const bootstrap = async () => {
      setStatus("Starting session…");
      try {
        const resp = await fetch("/api/labs/conversation/session", {
          method: "POST",
          credentials: "include",
        });
        const data = await resp.json();
        if (!resp.ok || data?.error) {
          throw new Error(data?.error || "Failed to start session");
        }
        setSession({ sessionId: data.sessionId, assistantName: data.assistantName, greeting: data.greeting });
        setStatus(`Session ready (${data.sessionId.slice(0, 6)}…)`);
      } catch (err) {
        setStatus((err as Error).message);
      }
    };
    void bootstrap();
    return () => {
      if (pollRef.current) {
        window.clearInterval(pollRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (!session?.sessionId) {
      return;
    }
    const poll = async () => {
      try {
        const resp = await fetch("/api/labs/conversation/uploads", { credentials: "include" });
        if (resp.ok) {
          const payload = await resp.json();
          setJobs(payload?.items || []);
        }
      } catch {
        /* ignore */
      }
    };
    void poll();
    pollRef.current = window.setInterval(poll, 4000);
    return () => {
      if (pollRef.current) {
        window.clearInterval(pollRef.current);
      }
    };
  }, [session?.sessionId]);

  const handleUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setStatus(`Uploading ${file.name}…`);
    const data = new FormData();
    data.append("file", file);
    data.append("description", "Conversation Lab tester upload");
    try {
      const resp = await fetch("/api/labs/conversation/ingest", {
        method: "POST",
        credentials: "include",
        body: data,
      });
      const payload = await resp.json();
      if (!resp.ok || payload?.ok === false) {
        throw new Error(payload?.error || "Upload failed");
      }
      setStatus(`Uploaded ${file.name}. Waiting for processing…`);
      void (async () => {
        const statusResp = await fetch("/api/labs/conversation/uploads", { credentials: "include" });
        if (statusResp.ok) {
          const jobsPayload = await statusResp.json();
          setJobs(jobsPayload?.items || []);
        }
      })();
    } catch (err) {
      setStatus((err as Error).message);
    } finally {
      event.target.value = "";
    }
  };

  const sendChat = async () => {
    setChatReply("Thinking…");
    try {
      const resp = await fetch("/api/labs/conversation/chat", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: chatPrompt }),
      });
      const payload = await resp.json();
      if (!resp.ok || payload?.error) {
        throw new Error(payload?.error || "Chat failed");
      }
      setChatReply(payload.reply);
    } catch (err) {
      setChatReply((err as Error).message);
    }
  };

  return (
    <div className="lab-tester">
      <header>
        <h1>Conversation Lab Tester</h1>
        <p>{status || "Session not started"}</p>
      </header>

      <section>
        <h2>1. Upload a file</h2>
        <input type="file" onChange={handleUpload} accept=".txt,.csv,.json,.xlsx" />
        <ul className="job-list">
          {jobs.map((job) => (
            <li key={job.jobId}>
              <strong>{job.filename}</strong> — {job.status}
              {job.summary ? <span className="summary"> ({job.summary})</span> : null}
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2>2. Send a prompt</h2>
        <textarea value={chatPrompt} onChange={(e) => setChatPrompt(e.target.value)} rows={4} />
        <button type="button" onClick={sendChat} disabled={!session}>
          Ask Quell-AI
        </button>
        {chatReply && <pre className="chat-reply">{chatReply}</pre>}
      </section>
    </div>
  );
}
