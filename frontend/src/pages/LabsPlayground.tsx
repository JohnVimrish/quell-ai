import { useCallback, useEffect, useMemo, useState } from "react";
import type { ChangeEvent, FormEvent } from "react";

type ApiStatus = {
  provider: string;
  chatModel: string;
  embedModel: string;
  embedDim: number;
  hasApiKey: boolean;
  canUseOpenAI: boolean;
};

type MCPComponent = {
  id: string;
  label: string;
  content: string;
};

type RagDocument = {
  id: string;
  title: string;
  content: string;
};

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

type NotebookFile = {
  id: string;
  name: string;
  content: string;
  encoding: "base64" | "text";
};

type RagResponse = {
  matches: Array<{ title: string; score: number; preview: string }>;
  answer: string;
  contextUsed: string;
};

const EMPTY_STATUS: ApiStatus = {
  provider: "",
  chatModel: "",
  embedModel: "",
  embedDim: 0,
  hasApiKey: false,
  canUseOpenAI: false,
};

const DEFAULT_SYSTEM_PROMPT =
  "You are Quell AI's design-time assistant. Provide clear, actionable responses.";

function createId(prefix: string): string {
  return `${prefix}-${Math.random().toString(36).slice(2, 10)}`;
}

async function fetchJson<T>(input: RequestInfo, init?: RequestInit): Promise<T> {
  const response = await fetch(input, init);
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    const message = typeof detail?.error === "string" ? detail.error : `Request failed (${response.status})`;
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export default function LabsPlayground() {
  const [apiStatus, setApiStatus] = useState<ApiStatus>(EMPTY_STATUS);
  const [apiStatusMessage, setApiStatusMessage] = useState<string>("");
  const [apiKeyInput, setApiKeyInput] = useState<string>("");
  const [statusLoading, setStatusLoading] = useState<boolean>(false);

  const [mcpInstructions, setMcpInstructions] = useState<string>(DEFAULT_SYSTEM_PROMPT);
  const [mcpComponents, setMcpComponents] = useState<MCPComponent[]>([
    { id: createId("mcp"), label: "Objective", content: "" },
    { id: createId("mcp"), label: "Constraints", content: "" },
  ]);
  const [mcpOutput, setMcpOutput] = useState<{ response: string; combinedPrompt: string } | null>(null);
  const [mcpLoading, setMcpLoading] = useState<boolean>(false);
  const [mcpError, setMcpError] = useState<string>("");

  const [ragDocs, setRagDocs] = useState<RagDocument[]>([]);
  const [ragNewDoc, setRagNewDoc] = useState<{ title: string; content: string }>({ title: "", content: "" });
  const [ragQuery, setRagQuery] = useState<string>("");
  const [ragLoading, setRagLoading] = useState<boolean>(false);
  const [ragError, setRagError] = useState<string>("");
  const [ragResult, setRagResult] = useState<RagResponse | null>(null);

  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    { role: "assistant", content: "Welcome! Ask a question to see the assistant in action." },
  ]);
  const [chatInput, setChatInput] = useState<string>("");
  const [chatLoading, setChatLoading] = useState<boolean>(false);
  const [chatError, setChatError] = useState<string>("");

  const [notebookNotes, setNotebookNotes] = useState<string[]>([""]);
  const [notebookFiles, setNotebookFiles] = useState<NotebookFile[]>([]);
  const [notebookQuestion, setNotebookQuestion] = useState<string>("");
  const [notebookLoading, setNotebookLoading] = useState<boolean>(false);
  const [notebookError, setNotebookError] = useState<string>("");
  const [notebookResult, setNotebookResult] = useState<RagResponse | null>(null);

  const [speechText, setSpeechText] = useState<string>("");
  const [speechLoading, setSpeechLoading] = useState<boolean>(false);
  const [speechError, setSpeechError] = useState<string>("");
  const [speechAudio, setSpeechAudio] = useState<string | null>(null);

  const hasDocuments = ragDocs.length > 0;
  const canUseOpenAI = apiStatus.canUseOpenAI && apiStatus.hasApiKey;

  const refreshStatus = useCallback(async () => {
    setStatusLoading(true);
    setApiStatusMessage("");
    try {
      const status = await fetchJson<ApiStatus>("/api/labs/status");
      setApiStatus(status);
      setApiStatusMessage(
        status.canUseOpenAI
          ? "OpenAI access is ready."
          : "OpenAI access is currently offline. Requests will fall back to local heuristics."
      );
    } catch (error) {
      setApiStatus(EMPTY_STATUS);
      setApiStatusMessage(error instanceof Error ? error.message : "Unable to load status.");
    } finally {
      setStatusLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshStatus();
    try {
      const storedKey = localStorage.getItem("qa_openai_key");
      if (storedKey) {
        setApiKeyInput(storedKey);
      }
    } catch {
      // ignore
    }
  }, [refreshStatus]);

  const handleStoreKeyLocal = useCallback(() => {
    try {
      if (apiKeyInput.trim()) {
        localStorage.setItem("qa_openai_key", apiKeyInput.trim());
      } else {
        localStorage.removeItem("qa_openai_key");
      }
      setApiStatusMessage("Key stored locally. Send it to the server when ready.");
    } catch (error) {
      setApiStatusMessage(error instanceof Error ? error.message : "Unable to access local storage.");
    }
  }, [apiKeyInput]);

  const handleSendKeyToServer = useCallback(
    async (event: FormEvent) => {
      event.preventDefault();
      setStatusLoading(true);
      setApiStatusMessage("");
      try {
        await fetchJson<ApiStatus>("/api/labs/api-key", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ apiKey: apiKeyInput }),
        });
        setApiStatusMessage("Server connection updated.");
        await refreshStatus();
      } catch (error) {
        setApiStatusMessage(error instanceof Error ? error.message : "Failed to update server key.");
      } finally {
        setStatusLoading(false);
      }
    },
    [apiKeyInput, refreshStatus]
  );

  const updateComponentLabel = useCallback((id: string, label: string) => {
    setMcpComponents((prev) => prev.map((component) => (component.id === id ? { ...component, label } : component)));
  }, []);

  const updateComponentContent = useCallback((id: string, content: string) => {
    setMcpComponents((prev) => prev.map((component) => (component.id === id ? { ...component, content } : component)));
  }, []);

  const addComponent = useCallback(() => {
    setMcpComponents((prev) => [...prev, { id: createId("mcp"), label: "New Component", content: "" }]);
  }, []);

  const removeComponent = useCallback((id: string) => {
    setMcpComponents((prev) => (prev.length <= 1 ? prev : prev.filter((component) => component.id !== id)));
  }, []);

  const handleRunMcp = useCallback(
    async (event: FormEvent) => {
      event.preventDefault();
      setMcpError("");
      setMcpOutput(null);
      setMcpLoading(true);
      try {
        const payload = {
          instructions: mcpInstructions,
          components: mcpComponents.map(({ label, content }) => ({ label, content })),
        };
        const result = await fetchJson<{
          systemPrompt: string;
          combinedPrompt: string;
          response: string;
        }>("/api/labs/mcp/run", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        setMcpOutput({ response: result.response, combinedPrompt: result.combinedPrompt });
      } catch (error) {
        setMcpError(error instanceof Error ? error.message : "Unable to run multi-component prompt.");
      } finally {
        setMcpLoading(false);
      }
    },
    [mcpComponents, mcpInstructions]
  );

  const handleAddDocument = useCallback(() => {
    if (!ragNewDoc.content.trim()) {
      setRagError("Add content before saving the document.");
      return;
    }
    setRagDocs((prev) => [
      ...prev,
      {
        id: createId("doc"),
        title: ragNewDoc.title.trim() || `Document ${prev.length + 1}`,
        content: ragNewDoc.content.trim(),
      },
    ]);
    setRagNewDoc({ title: "", content: "" });
    setRagError("");
  }, [ragNewDoc]);

  const handleRemoveDocument = useCallback((id: string) => {
    setRagDocs((prev) => prev.filter((doc) => doc.id !== id));
  }, []);

  const handleDocFile = useCallback((event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    file
      .text()
      .then((text) => {
        setRagDocs((prev) => [
          ...prev,
          { id: createId("doc"), title: file.name || `Document ${prev.length + 1}`, content: text },
        ]);
        setRagError("");
      })
      .catch(() => setRagError("Unable to read the selected file."));
  }, []);

  const handleRagQuery = useCallback(
    async (event: FormEvent) => {
      event.preventDefault();
      setRagError("");
      setRagResult(null);
      if (!ragDocs.length) {
        setRagError("Add at least one document before querying.");
        return;
      }
      if (!ragQuery.trim()) {
        setRagError("Enter a query to continue.");
        return;
      }
      setRagLoading(true);
      try {
        const payload = {
          query: ragQuery,
          documents: ragDocs.map(({ title, content }) => ({ title, content })),
        };
        const result = await fetchJson<RagResponse>("/api/labs/rag/workbench", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        setRagResult(result);
      } catch (error) {
        setRagError(error instanceof Error ? error.message : "Unable to run RAG query.");
      } finally {
        setRagLoading(false);
      }
    },
    [ragDocs, ragQuery]
  );

  const handleChatSend = useCallback(
    async (event: FormEvent) => {
      event.preventDefault();
      setChatError("");
      const trimmed = chatInput.trim();
      if (!trimmed) return;
      const userMessage: ChatMessage = { role: "user", content: trimmed };
      const conversation: ChatMessage[] = [...chatMessages, userMessage];
      setChatMessages(conversation);
      setChatInput("");
      setChatLoading(true);
      try {
        const result = await fetchJson<{ reply: string }>("/api/labs/chat/session", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ messages: conversation }),
        });
        setChatMessages((prev) => [...prev, { role: "assistant", content: result.reply }]);
      } catch (error) {
        setChatError(error instanceof Error ? error.message : "Unable to contact assistant.");
        setChatMessages((prev) => [...prev, { role: "assistant", content: "The assistant is unavailable right now." }]);
      } finally {
        setChatLoading(false);
      }
    },
    [chatInput, chatMessages]
  );

  const updateNote = useCallback((index: number, value: string) => {
    setNotebookNotes((prev) => prev.map((note, idx) => (idx === index ? value : note)));
  }, []);

  const addNote = useCallback(() => {
    setNotebookNotes((prev) => [...prev, ""]);
  }, []);

  const removeNote = useCallback((index: number) => {
    setNotebookNotes((prev) => (prev.length <= 1 ? prev : prev.filter((_, idx) => idx !== index)));
  }, []);

  const handleNotebookFile = useCallback((event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const result = typeof reader.result === "string" ? reader.result : "";
      setNotebookFiles((prev) => [
        ...prev,
        {
          id: createId("file"),
          name: file.name || `Upload-${prev.length + 1}`,
          content: result,
          encoding: result.startsWith("data:") ? "base64" : "text",
        },
      ]);
    };
    reader.onerror = () => setNotebookError("Unable to read the uploaded file.");
    reader.readAsDataURL(file);
  }, []);

  const removeNotebookFile = useCallback((id: string) => {
    setNotebookFiles((prev) => prev.filter((file) => file.id !== id));
  }, []);

  const handleNotebookQuery = useCallback(
    async (event: FormEvent) => {
      event.preventDefault();
      setNotebookError("");
      setNotebookResult(null);
      if (!notebookQuestion.trim()) {
        setNotebookError("Ask the assistant a question.");
        return;
      }
      if (!notebookNotes.some((note) => note.trim()) && notebookFiles.length === 0) {
        setNotebookError("Add at least one note or file.");
        return;
      }
      setNotebookLoading(true);
      try {
        const payload = {
          question: notebookQuestion,
          notes: notebookNotes.filter((note) => note.trim()),
          files: notebookFiles.map(({ name, content, encoding }) => ({ name, content, encoding })),
        };
        const result = await fetchJson<RagResponse>("/api/labs/notebook/respond", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        setNotebookResult(result);
      } catch (error) {
        setNotebookError(error instanceof Error ? error.message : "Notebook assistant is unavailable.");
      } finally {
        setNotebookLoading(false);
      }
    },
    [notebookFiles, notebookNotes, notebookQuestion]
  );

  const handleSpeak = useCallback(
    async (event: FormEvent) => {
      event.preventDefault();
      setSpeechError("");
      setSpeechAudio(null);
      if (!speechText.trim()) {
        setSpeechError("Provide text for the assistant to narrate.");
        return;
      }
      setSpeechLoading(true);
      try {
        const result = await fetchJson<{ audio: string; sampleRate: number; contentType: string; note: string }>(
          "/api/labs/chat/speak",
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: speechText }),
          }
        );
        setSpeechAudio(`data:${result.contentType};base64,${result.audio}`);
      } catch (error) {
        setSpeechError(error instanceof Error ? error.message : "Unable to synthesize audio.");
      } finally {
        setSpeechLoading(false);
      }
    },
    [speechText]
  );

  const capabilitySummary = useMemo(() => {
    if (!apiStatus.provider) {
      return "Backend pipeline is running in local fallback mode.";
    }
    const provider = apiStatus.provider || "fallback";
    return `Provider: ${provider} — chat model: ${apiStatus.chatModel}, embed model: ${apiStatus.embedModel} (dim ${apiStatus.embedDim}).`;
  }, [apiStatus]);

  return (
    <div className="labs-playground">
      <header className="glass-panel" style={{ padding: "32px", marginBottom: "24px" }}>
        <h1 style={{ marginBottom: "12px" }}>AI Blueprint Playground</h1>
        <p style={{ marginBottom: 0 }}>
          This sandbox focuses on functionality. Use it to wire together OpenAI credentials, experiment with
          multi-component prompting, retrieval workflows, conversational flows, and notebook-style file reasoning.
        </p>
      </header>

      <section className="glass-panel" style={{ padding: "28px", marginBottom: "28px" }}>
        <h2>1. Configure OpenAI Connectivity</h2>
        <p style={{ marginBottom: "12px" }}>
          Provide your OpenAI API key to unlock cloud-backed completions. The key is stored locally (for debugging) and
          can optionally be pushed into the running Flask process.
        </p>
        <form onSubmit={handleSendKeyToServer} className="labs-grid" style={{ gap: "16px" }}>
          <label style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            <span>OpenAI API Key</span>
            <input
              type="password"
              value={apiKeyInput}
              onChange={(event) => setApiKeyInput(event.target.value)}
              placeholder="sk-..."
              className="input"
            />
          </label>
          <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
            <button type="button" className="button-outline" onClick={handleStoreKeyLocal}>
              Store in browser
            </button>
            <button type="submit" className="button-engage" disabled={statusLoading}>
              {statusLoading ? "Updating..." : "Send to backend"}
            </button>
            <button type="button" className="button-outline" onClick={refreshStatus}>
              Refresh status
            </button>
          </div>
        </form>
        <p style={{ marginTop: "12px", color: "var(--color-grey-600)" }}>{capabilitySummary}</p>
        {apiStatusMessage && (
          <p style={{ marginTop: "8px", color: canUseOpenAI ? "var(--color-green-600)" : "var(--color-orange-500)" }}>
            {apiStatusMessage}
          </p>
        )}
      </section>

      <section className="glass-panel" style={{ padding: "28px", marginBottom: "28px" }}>
        <h2>2. Multi-Component Prompting (MCP)</h2>
        <p style={{ marginBottom: "12px" }}>
          Break complex instructions into labeled components. The playground sends the combined prompt to the backend
          MCP endpoint so you can verify orchestration logic before wiring production pipelines.
        </p>
        <form onSubmit={handleRunMcp} className="labs-grid" style={{ gap: "16px" }}>
          <label style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            <span>System guardrails</span>
            <textarea
              className="textarea"
              rows={3}
              value={mcpInstructions}
              onChange={(event) => setMcpInstructions(event.target.value)}
            />
          </label>
          <div style={{ display: "grid", gap: "12px" }}>
            {mcpComponents.map((component) => (
              <div key={component.id} className="labs-card" style={{ padding: "16px" }}>
                <div style={{ display: "flex", gap: "12px", marginBottom: "12px" }}>
                  <input
                    className="input"
                    value={component.label}
                    onChange={(event) => updateComponentLabel(component.id, event.target.value)}
                    placeholder="Component label"
                  />
                  <button
                    type="button"
                    className="button-outline"
                    onClick={() => removeComponent(component.id)}
                    disabled={mcpComponents.length <= 1}
                  >
                    Remove
                  </button>
                </div>
                <textarea
                  className="textarea"
                  rows={4}
                  placeholder="Component content..."
                  value={component.content}
                  onChange={(event) => updateComponentContent(component.id, event.target.value)}
                />
              </div>
            ))}
          </div>
          <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
            <button type="button" className="button-outline" onClick={addComponent}>
              Add component
            </button>
            <button type="submit" className="button-engage" disabled={mcpLoading}>
              {mcpLoading ? "Generating..." : "Run MCP"}
            </button>
          </div>
        </form>
        {mcpError && <p className="labs-error" style={{ marginTop: "12px" }}>{mcpError}</p>}
        {mcpOutput && (
          <div className="labs-card" style={{ marginTop: "16px" }}>
            <h3>MCP Output</h3>
            <p style={{ whiteSpace: "pre-wrap" }}>{mcpOutput.response}</p>
            <details style={{ marginTop: "12px" }}>
              <summary>View combined prompt</summary>
              <pre style={{ whiteSpace: "pre-wrap" }}>{mcpOutput.combinedPrompt}</pre>
            </details>
          </div>
        )}
      </section>

      <section className="glass-panel" style={{ padding: "28px", marginBottom: "28px" }}>
        <h2>3. Retrieval-Augmented Generation (RAG)</h2>
        <p style={{ marginBottom: "12px" }}>
          Load documents, issue a question, and inspect the top matches with the generated answer. This section mirrors
          the backend helper that combines embeddings with prompt synthesis.
        </p>
        <form onSubmit={handleRagQuery} className="labs-grid" style={{ gap: "16px" }}>
          <div className="labs-card" style={{ padding: "16px" }}>
            <h3>Add document</h3>
            <label style={{ display: "flex", flexDirection: "column", gap: "6px", marginBottom: "12px" }}>
              <span>Title</span>
              <input
                className="input"
                value={ragNewDoc.title}
                onChange={(event) => setRagNewDoc((prev) => ({ ...prev, title: event.target.value }))}
              />
            </label>
            <label style={{ display: "flex", flexDirection: "column", gap: "6px", marginBottom: "12px" }}>
              <span>Content</span>
              <textarea
                className="textarea"
                rows={4}
                value={ragNewDoc.content}
                onChange={(event) => setRagNewDoc((prev) => ({ ...prev, content: event.target.value }))}
              />
            </label>
            <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
              <button type="button" className="button-outline" onClick={handleAddDocument}>
                Save document
              </button>
              <label className="button-outline" style={{ cursor: "pointer" }}>
                Upload text file
                <input type="file" accept=".txt,.md,.json" hidden onChange={handleDocFile} />
              </label>
            </div>
          </div>
          {!!ragDocs.length && (
            <div className="labs-card" style={{ padding: "16px" }}>
              <h3>Current knowledge base ({ragDocs.length})</h3>
              <ul style={{ paddingLeft: "20px", margin: 0 }}>
                {ragDocs.map((doc) => (
                  <li key={doc.id} style={{ marginBottom: "8px" }}>
                    <strong>{doc.title}</strong>{" "}
                    <button type="button" className="button-inline" onClick={() => handleRemoveDocument(doc.id)}>
                      remove
                    </button>
                    <p style={{ margin: "4px 0 0", color: "var(--color-grey-600)" }}>
                      {doc.content.slice(0, 160)}{doc.content.length > 160 ? "..." : ""}
                    </p>
                  </li>
                ))}
              </ul>
            </div>
          )}
          <label style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            <span>Ask a question</span>
            <input
              className="input"
              value={ragQuery}
              onChange={(event) => setRagQuery(event.target.value)}
              placeholder="e.g. Summarize the escalation policy."
            />
          </label>
          <button type="submit" className="button-engage" disabled={ragLoading || !hasDocuments}>
            {ragLoading ? "Searching..." : "Run retrieval"}
          </button>
        </form>
        {ragError && <p className="labs-error" style={{ marginTop: "12px" }}>{ragError}</p>}
        {ragResult && (
          <div className="labs-card" style={{ marginTop: "16px" }}>
            <h3>Answer</h3>
            <p style={{ whiteSpace: "pre-wrap" }}>{ragResult.answer}</p>
            <details style={{ marginTop: "12px" }}>
              <summary>Top matches</summary>
              <ul style={{ paddingLeft: "20px", marginTop: "8px" }}>
                {ragResult.matches.map((match) => (
                  <li key={match.title} style={{ marginBottom: "8px" }}>
                    <strong>{match.title}</strong> — score {match.score}
                    <p style={{ margin: "4px 0 0", color: "var(--color-grey-600)" }}>{match.preview}</p>
                  </li>
                ))}
              </ul>
            </details>
          </div>
        )}
      </section>

      <section className="glass-panel" style={{ padding: "28px", marginBottom: "28px" }}>
        <h2>4. Conversational Sandbox</h2>
        <p style={{ marginBottom: "12px" }}>
          Test the lightweight chatbot endpoint. Add messages to inspect how state is passed to the backend.
        </p>
        <div className="labs-card" style={{ padding: "16px" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: "12px", maxHeight: "320px", overflow: "auto" }}>
            {chatMessages.map((message, index) => (
              <div
                key={`${message.role}-${index}`}
                className={message.role === "user" ? "labs-chat-user" : "labs-chat-assistant"}
                style={{
                  alignSelf: message.role === "user" ? "flex-end" : "flex-start",
                  background: message.role === "user" ? "var(--accent-pastel-green)" : "var(--color-grey-100)",
                  borderRadius: "16px",
                  padding: "12px 16px",
                }}
              >
                <strong style={{ display: "block", marginBottom: "6px" }}>
                  {message.role === "user" ? "You" : "Assistant"}
                </strong>
                <span style={{ whiteSpace: "pre-wrap" }}>{message.content}</span>
              </div>
            ))}
          </div>
          <form onSubmit={handleChatSend} style={{ display: "flex", gap: "12px", marginTop: "16px" }}>
            <input
              className="input"
              value={chatInput}
              onChange={(event) => setChatInput(event.target.value)}
              placeholder="Ask something..."
            />
            <button type="submit" className="button-engage" disabled={chatLoading}>
              {chatLoading ? "Replying..." : "Send"}
            </button>
          </form>
          {chatError && <p className="labs-error" style={{ marginTop: "12px" }}>{chatError}</p>}
        </div>
      </section>

      <section className="glass-panel" style={{ padding: "28px", marginBottom: "28px" }}>
        <h2>5. Notebook “LLM Googles”</h2>
        <p style={{ marginBottom: "12px" }}>
          Combine inline notes and uploads into a scratchpad, then ask the assistant to reason across them. Useful for
          validating file ingestion strategies.
        </p>
        <form onSubmit={handleNotebookQuery} className="labs-grid" style={{ gap: "16px" }}>
          <div className="labs-card" style={{ padding: "16px" }}>
            <h3>Notes</h3>
            <div style={{ display: "grid", gap: "12px" }}>
              {notebookNotes.map((note, index) => (
                <div key={`note-${index}`} style={{ display: "flex", gap: "12px" }}>
                  <textarea
                    className="textarea"
                    rows={3}
                    value={note}
                    onChange={(event) => updateNote(index, event.target.value)}
                    placeholder="Add context, decisions, or hypotheses..."
                  />
                  <button
                    type="button"
                    className="button-outline"
                    onClick={() => removeNote(index)}
                    disabled={notebookNotes.length <= 1}
                    style={{ alignSelf: "flex-start" }}
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
            <button type="button" className="button-outline" onClick={addNote} style={{ marginTop: "12px" }}>
              Add another note
            </button>
          </div>
          <div className="labs-card" style={{ padding: "16px" }}>
            <h3>Uploaded files ({notebookFiles.length})</h3>
            <label className="button-outline" style={{ cursor: "pointer", marginBottom: "12px", display: "inline-block" }}>
              Upload file
              <input type="file" hidden onChange={handleNotebookFile} />
            </label>
            <ul style={{ paddingLeft: "20px", margin: 0 }}>
              {notebookFiles.map((file) => (
                <li key={file.id} style={{ marginBottom: "8px" }}>
                  {file.name}{" "}
                  <button type="button" className="button-inline" onClick={() => removeNotebookFile(file.id)}>
                    remove
                  </button>
                </li>
              ))}
            </ul>
          </div>
          <label style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            <span>Ask the notebook</span>
            <input
              className="input"
              value={notebookQuestion}
              onChange={(event) => setNotebookQuestion(event.target.value)}
              placeholder="e.g. Summarize the key decisions from these notes."
            />
          </label>
          <button type="submit" className="button-engage" disabled={notebookLoading}>
            {notebookLoading ? "Analyzing..." : "Run notebook assistant"}
          </button>
        </form>
        {notebookError && <p className="labs-error" style={{ marginTop: "12px" }}>{notebookError}</p>}
        {notebookResult && (
          <div className="labs-card" style={{ marginTop: "16px" }}>
            <h3>Notebook answer</h3>
            <p style={{ whiteSpace: "pre-wrap" }}>{notebookResult.answer}</p>
            <details style={{ marginTop: "12px" }}>
              <summary>Context used</summary>
              <pre style={{ whiteSpace: "pre-wrap" }}>{notebookResult.contextUsed}</pre>
            </details>
          </div>
        )}
      </section>

      <section className="glass-panel" style={{ padding: "28px", marginBottom: "28px" }}>
        <h2>6. Optional: Speech Preview</h2>
        <p style={{ marginBottom: "12px" }}>
          Trigger the placeholder audio endpoint. This does not clone voices; it returns a synthesised tone so you can
          confirm transport and playback before integrating a production-grade TTS provider.
        </p>
        <form onSubmit={handleSpeak} className="labs-grid" style={{ gap: "16px" }}>
          <textarea
            className="textarea"
            rows={3}
            value={speechText}
            onChange={(event) => setSpeechText(event.target.value)}
            placeholder="Text to narrate..."
          />
          <button type="submit" className="button-engage" disabled={speechLoading}>
            {speechLoading ? "Generating audio..." : "Generate preview audio"}
          </button>
        </form>
        {speechError && <p className="labs-error" style={{ marginTop: "12px" }}>{speechError}</p>}
        {speechAudio && (
          <div style={{ marginTop: "16px" }}>
            <audio controls src={speechAudio} />
            <p style={{ marginTop: "8px", color: "var(--color-grey-600)" }}>
              Audio preview generated locally. Swap the backend implementation with production speech synthesis when ready.
            </p>
          </div>
        )}
      </section>
    </div>
  );
}




