import { useEffect, useRef, useState } from "react";
import "./ConversationLab.css";

const ACCEPTED_FILE_TYPES = [".txt", ".csv", ".json", ".xlsx"];
const ASSISTANT_NAME = "Quell-Ai";
const LAB_NAME_STORAGE_KEY = "qlx_lab_display_name";
const LAB_CHAT_STORAGE_KEY = "qlx_lab_chat_history";

type SessionInfo = {
  userId: number;
  sessionId: string;
  assistantName: string;
  greeting: string;
  hasName: boolean;
  displayName?: string | null;
};

type ChatRole = "user" | "assistant";

type AttachmentInsight = {
  filename: string;
  fileType: string;
  summary: string;
  analytics: Record<string, any>;
  concepts: Record<string, any>;
  translated: boolean;
};

type ChatMessage = {
  id: string;
  role: ChatRole;
  text: string;
  timestamp: string;
  attachment?: AttachmentInsight;
  senderName?: string;
  pending?: boolean;
};

type StoredChatHistory = {
  sessionId: string;
  history: ChatMessage[];
};

const generateId = () => `msg-${Date.now()}-${Math.random().toString(16).slice(2)}`;
const formatTimestamp = () => new Date().toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });

const loadStoredChatHistory = (): StoredChatHistory | null => {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(LAB_CHAT_STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as StoredChatHistory;
  } catch {
    return null;
  }
};

const persistChatHistory = (sessionId: string, history: ChatMessage[]) => {
  if (typeof window === "undefined") return;
  try {
    const payload: StoredChatHistory = {
      sessionId,
      history: history.slice(-15),
    };
    window.localStorage.setItem(LAB_CHAT_STORAGE_KEY, JSON.stringify(payload));
  } catch {
    // storage might be disabled
  }
};

const clearStoredChatHistory = () => {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.removeItem(LAB_CHAT_STORAGE_KEY);
  } catch {
    // ignore
  }
};

export default function ConversationLab() {
  const [sessionInfo, setSessionInfo] = useState<SessionInfo | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [initializing, setInitializing] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [attachGlow, setAttachGlow] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    initializeSession();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (!sessionInfo?.sessionId || messages.length === 0) {
      return;
    }
    persistChatHistory(sessionInfo.sessionId, messages);
  }, [messages, sessionInfo?.sessionId]);

  const readStoredName = (): string => {
    if (typeof window === "undefined") return "";
    try {
      return window.localStorage.getItem(LAB_NAME_STORAGE_KEY) || "";
    } catch {
      return "";
    }
  };

  const persistDisplayName = (value: string) => {
    if (typeof window === "undefined") return;
    try {
      window.localStorage.setItem(LAB_NAME_STORAGE_KEY, value);
    } catch {
      // storage might be disabled
    }
  };

  const restoreStoredName = async (storedName: string) => {
    try {
      await setNameOnServer(storedName, { silent: true });
      setSessionInfo((prev) =>
        prev
          ? {
              ...prev,
              hasName: true,
              displayName: storedName,
            }
          : prev,
      );
    } catch (err) {
      console.warn("Failed to restore stored Conversation Lab name", err);
    }
  };

  async function initializeSession() {
    setInitializing(true);
    setError(null);
    try {
      const response = await fetch("/api/labs/conversation/session", {
        method: "POST",
        credentials: "include",
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data?.error || "Failed to initialize Conversation Lab session.");
      }
      setSessionInfo(data);

      const stored = loadStoredChatHistory();
      if (stored && stored.sessionId === data.sessionId && stored.history?.length) {
        setMessages(stored.history);
      } else {
        clearStoredChatHistory();
        setMessages([
          {
            id: generateId(),
            role: "assistant",
            text: data.greeting,
            timestamp: formatTimestamp(),
            senderName: data.assistantName ?? ASSISTANT_NAME,
          },
        ]);
      }
    } catch (err) {
      const fallback = err instanceof Error ? err.message : "Unable to start the session.";
      setError(fallback);
      clearStoredChatHistory();
      setMessages([
        {
          id: generateId(),
          role: "assistant",
          text: `${ASSISTANT_NAME} here. ${fallback}`,
          timestamp: formatTimestamp(),
        },
      ]);
    } finally {
      setInitializing(false);
    }
  }

  const needsName = Boolean(sessionInfo && !sessionInfo.hasName);

  const buildAssistantMessage = (text: string, overrides?: Partial<ChatMessage>): ChatMessage => {
    const base: ChatMessage = {
      id: overrides?.id ?? generateId(),
      role: "assistant",
      text,
      timestamp: overrides?.timestamp ?? formatTimestamp(),
      senderName: sessionInfo?.assistantName ?? ASSISTANT_NAME,
    };
    return { ...base, ...overrides };
  };

  const showThinkingBubble = () => {
    const placeholder = buildAssistantMessage("Thinking with the Ollama model…", { pending: true });
    const placeholderId = placeholder.id;
    setMessages((prev) => [...prev, placeholder]);
    return placeholderId;
  };

  const resolveAssistantMessage = (
    text: string,
    options?: { placeholderId?: string; attachment?: AttachmentInsight },
  ) => {
    const message = buildAssistantMessage(text, {
      id: options?.placeholderId,
      pending: false,
      attachment: options?.attachment,
    });
    if (!options?.placeholderId) {
      setMessages((prev) => [...prev, message]);
      return;
    }
    setMessages((prev) => {
      let replaced = false;
      const next = prev.map((entry) => {
        if (entry.id === message.id) {
          replaced = true;
          return message;
        }
        return entry;
      });
      return replaced ? next : [...next, message];
    });
  };

  useEffect(() => {
    if (!sessionInfo) return;
    if (sessionInfo.displayName) {
      persistDisplayName(sessionInfo.displayName);
      return;
    }
    if (!sessionInfo.hasName) {
      const stored = readStoredName();
      if (stored) {
        void restoreStoredName(stored);
      }
    }
  }, [sessionInfo]);

  const handleSend = async () => {
    if (!sessionInfo) return;
    const trimmed = draft.trim();
    if (!trimmed || isSending || isUploading) return;

    setDraft("");
    setIsSending(true);
    setError(null);

    const userMessage: ChatMessage = {
      id: generateId(),
      role: "user",
      text: trimmed,
      timestamp: formatTimestamp(),
    };
    setMessages((prev) => [...prev, userMessage]);

    let placeholderId: string | undefined;

    try {
      if (needsName) {
        const nameResponse = await setNameOnServer(trimmed);
        setSessionInfo((prev) =>
          prev
            ? {
                ...prev,
                hasName: true,
                displayName: nameResponse.displayName,
              }
            : prev,
        );
        setMessages((prev) => [...prev, buildAssistantMessage(nameResponse.assistantReply)]);
      } else {
        placeholderId = showThinkingBubble();
        const chatResponse = await sendChat(trimmed);
        resolveAssistantMessage(chatResponse.reply, { placeholderId });
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unable to send message.";
      setError(message);
      resolveAssistantMessage("I hit a snag while reaching the model. Please try again in a moment.", {
        placeholderId,
      });
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter") {
      event.preventDefault();
      handleSend();
    }
  };

  const handleAttachmentButton = () => {
    if (!initializing) {
      setAttachGlow(true);
      window.setTimeout(() => setAttachGlow(false), 900);
      fileInputRef.current?.click();
    }
  };

  const handleFileSelection = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) {
      return;
    }

    setError(null);
    setIsUploading(true);

    for (const file of Array.from(files)) {
      const ext = `.${file.name.split(".").pop()?.toLowerCase() || ""}`;
      if (!ACCEPTED_FILE_TYPES.includes(ext)) {
        setError(`Unsupported file type: ${ext}. Please upload ${ACCEPTED_FILE_TYPES.join(", ")}`);
        continue;
      }

      const userMessage: ChatMessage = {
        id: generateId(),
        role: "user",
        text: `Uploading ${file.name} for review...`,
        timestamp: formatTimestamp(),
      };

      setMessages((prev) => [...prev, userMessage]);

      try {
        const uploadResult = await ingestFile(file);
        const attachment: AttachmentInsight = {
          filename: uploadResult.filename,
          fileType: uploadResult.fileType,
          summary: uploadResult.summary,
          analytics: uploadResult.analytics,
          concepts: uploadResult.concepts,
          translated: Boolean(uploadResult.translated),
        };

        const assistantMessage: ChatMessage = {
          ...buildAssistantMessage(`Here is a quick breakdown of ${uploadResult.filename}.`),
          attachment,
        };

        setMessages((prev) => [...prev, assistantMessage]);
      } catch (uploadError) {
        const message = uploadError instanceof Error ? uploadError.message : "Upload failed.";
        setError(message);
        setMessages((prev) => [
          ...prev,
          buildAssistantMessage(`I could not process ${file.name}: ${message}`),
        ]);
      }
    }

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
    setIsUploading(false);
  };

  const setNameOnServer = async (name: string, options?: { silent?: boolean }) => {
    const response = await fetch("/api/labs/conversation/name", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, message: name }),
    });
    const payload = await response.json();
    if (!response.ok || payload?.ok === false) {
      throw new Error(payload?.error || "Failed to store name.");
    }
    persistDisplayName(payload.displayName);
    return {
      ...(payload as { displayName: string; assistantReply: string; assistantName: string }),
      silent: options?.silent,
    };
  };

  const sendChat = async (message: string) => {
    const response = await fetch("/api/labs/conversation/chat", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    const payload = await response.json();
    if (!response.ok || payload?.error) {
      throw new Error(payload?.error || "Failed to reach Quell-Ai.");
    }
    return payload as { reply: string };
  };

  const ingestFile = async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("description", "Conversation Lab upload");

    const response = await fetch("/api/labs/conversation/ingest", {
      method: "POST",
      credentials: "include",
      body: formData,
    });

    const payload = await response.json();
    if (!response.ok || payload?.ok === false) {
      throw new Error(payload?.error || "Failed to process file");
    }
    return payload;
  };

  const attachmentSummary = (attachment: AttachmentInsight) => {
    const analytics = attachment.analytics || {};
    if ("row_count" in analytics) {
      return `${analytics.row_count} rows • ${analytics.column_count ?? 0} columns`;
    }
    if ("word_count" in analytics) {
      return `${analytics.word_count} words • ${analytics.line_count ?? 0} lines`;
    }
    return attachment.summary;
  };

  const attachmentChips = (attachment: AttachmentInsight) => {
    const chips: string[] = [];
    if (attachment.analytics?.row_count) {
      chips.push(`${attachment.analytics.row_count} rows`);
    }
    if (attachment.analytics?.column_count) {
      chips.push(`${attachment.analytics.column_count} columns`);
    }
    if (attachment.analytics?.word_count) {
      chips.push(`${attachment.analytics.word_count} words`);
    }
    const keyPhrase = attachment.concepts?.key_phrases?.[0];
    if (keyPhrase) {
      chips.push(`Key phrase: ${keyPhrase}`);
    }
    if (attachment.translated) {
      chips.push("Translated to English");
    }
    return chips.slice(0, 3);
  };

  const attachmentContext = ACCEPTED_FILE_TYPES.join(", ");

  if (initializing) {
    return (
      <div className="conversation-lab">
        <div className="clab-background" aria-hidden />
        <section className="clab-chat-shell">
          <div className="clab-loading">Preparing Conversation Lab...</div>
        </section>
      </div>
    );
  }

  return (
    <div className="conversation-lab">
      <div className="clab-background" aria-hidden />
      <section className="clab-chat-shell">
        <div className="clab-chat-panel">
          <header className="clab-chat-header">
            <div>
              <p className="clab-chat-title">Conversation stream</p>
              <p className="clab-chat-subtitle">
                Attach {attachmentContext} or type a natural question. Responses stay inside this lab.
              </p>
            </div>
            <div className="clab-chat-actions">
              <button
                type="button"
                className={`clab-attach-btn ${attachGlow ? "active" : ""}`}
                onClick={handleAttachmentButton}
                disabled={isUploading}
              >
                <span className="clab-attach-icon" aria-hidden>
                  📎
                </span>
                <span>Attach file</span>
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept={ACCEPTED_FILE_TYPES.join(",")}
                multiple
                hidden
                onChange={handleFileSelection}
              />
            </div>
          </header>

          {error && (
            <div className="clab-alert" role="status">
              {error}
            </div>
          )}

          <div className="clab-chat-messages">
            {messages.map((message) => (
              <div key={message.id} className={`clab-message ${message.role} ${message.pending ? "pending" : ""}`}>
                <div className="clab-avatar" aria-hidden>
                  {message.role === "assistant" ? "QA" : "You".slice(0, 2)}
                </div>
                <div className="clab-bubble">
                  <div className="clab-bubble-meta">
                    <span>{message.role === "assistant" ? ASSISTANT_NAME : sessionInfo?.displayName || "You"}</span>
                    <span>{message.timestamp}</span>
                  </div>
                  {message.pending ? (
                    <div className="clab-thinking" role="status" aria-live="polite">
                      <span className="clab-thinking-dots" aria-hidden>
                        <span />
                        <span />
                        <span />
                      </span>
                      <span>{message.text || "Thinking..."}</span>
                    </div>
                  ) : (
                    <p className="clab-message-text">{message.text}</p>
                  )}
                  {message.attachment && (
                    <div className="clab-attachment-card">
                      <div className="clab-attachment-header">
                        <div>
                          <span className="clab-attachment-name">{message.attachment.filename}</span>
                          <span className="clab-attachment-type">{message.attachment.fileType.toUpperCase()}</span>
                        </div>
                        <span>{attachmentSummary(message.attachment)}</span>
                      </div>
                      <p className="clab-attachment-summary">{message.attachment.summary}</p>
                      <div className="clab-attachment-chips">
                        {attachmentChips(message.attachment).map((chip) => (
                          <span key={chip}>{chip}</span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <div className="clab-chat-input">
            <input
              value={draft}
              placeholder={
                needsName ? "First, let me know your name so I can personalize things." : "Type a message..."
              }
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isSending || isUploading}
            />
            <button type="button" onClick={handleSend} disabled={isSending || isUploading}>
              {needsName ? "Share name" : "Send"}
            </button>
          </div>
        </div>

      </section>
    </div>
  );
}
