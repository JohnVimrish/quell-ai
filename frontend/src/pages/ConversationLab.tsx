import { useCallback, useEffect, useRef, useState } from "react";
import { io, type Socket } from "socket.io-client";
import "./ConversationLab.css";

const ACCEPTED_FILE_TYPES = [".txt", ".csv", ".json", ".xlsx"];
const ASSISTANT_NAME = "Quell-Ai";
const LAB_NAME_STORAGE_KEY = "qlx_lab_display_name";
const LAB_CHAT_STORAGE_KEY = "qlx_lab_chat_history";
const MAX_CACHED_FILES = 10;
const UPLOAD_ERROR_MESSAGES: Record<string, string> = {
  payload_missing: "Upload payload expired. Please re-upload the file.",
  validation_error: "The file format or size violated upload rules.",
  ingest_exception: "The ingestion service encountered an error.",
  pipeline_error: "The ingestion pipeline rejected this file.",
  embedding_failed: "Embedding generation failed; we will retry later.",
  openpyxl_missing: "Excel support is unavailable on the server. Contact support.",
};
const SOCKET_ENDPOINT = import.meta.env.DEV ? "http://localhost:5000" : undefined;

type MemoryReminder = {
  id: number;
  text: string;
  sourceDisplayName?: string | null;
  createdAt?: string | null;
};

type SessionInfo = {
  userId: number;
  sessionId: string;
  assistantName: string;
  greeting: string;
  hasName: boolean;
  displayName?: string | null;
  pendingMemories?: MemoryReminder[];
};

type NameResponse = {
  displayName: string;
  assistantReply: string;
  assistantName: string;
  pendingMemories: MemoryReminder[];
  silent: boolean;
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

type UploadJob = {
  id: number;
  sessionId?: string | null;
  filename: string;
  fileType: string;
  status: string;
  errorCode?: string | null;
  errorMessage?: string | null;
  summary?: string | null;
  analytics?: Record<string, any> | null;
  processedPreview?: string | null;
  language?: string | null;
  queuedAt?: string | null;
  startedAt?: string | null;
  finishedAt?: string | null;
  ragDocumentId?: number | null;
  progressStage?: string | null;
  progressDetail?: string | null;
  fileHash?: string | null;
  clientSignature?: string | null;
};

type UploadEnqueueResult = {
  jobId: number;
  filename: string;
  fileType: string;
  status: string;
};

type CachedUploadEntry = {
  file: File;
  aliases: Set<string>;
  signature: string;
  fallbackSignature: string;
};

const generateId = () => `msg-${Date.now()}-${Math.random().toString(16).slice(2)}`;
const formatTimestamp = () => new Date().toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
const formatIsoTimestamp = (value?: string | null) => {
  if (!value) {
    return formatTimestamp();
  }
  try {
    return new Date(value).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
  } catch {
    return formatTimestamp();
  }
};

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

const fallbackSignature = (file: File) => `${file.name}:${file.size}:${file.lastModified}`;

async function hashFile(file: File): Promise<string> {
  if (typeof window !== "undefined" && window.crypto?.subtle) {
    try {
      const buffer = await file.arrayBuffer();
      const digest = await window.crypto.subtle.digest("SHA-256", buffer);
      return Array.from(new Uint8Array(digest))
        .map((byte) => byte.toString(16).padStart(2, "0"))
        .join("");
    } catch {
      // fall through to string signature
    }
  }
  return fallbackSignature(file);
}

export default function ConversationLab() {
  const [sessionInfo, setSessionInfo] = useState<SessionInfo | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [initializing, setInitializing] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [attachGlow, setAttachGlow] = useState(false);
  const [uploadJobs, setUploadJobs] = useState<UploadJob[]>([]);
  const [queueDepth, setQueueDepth] = useState(0);
  const [queueLimit, setQueueLimit] = useState(5);
  const [retryingJobId, setRetryingJobId] = useState<number | null>(null);
  const socketRef = useRef<Socket | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const uploadCacheRef = useRef<Map<string, CachedUploadEntry>>(new Map());
  const aliasRef = useRef<Map<string, string>>(new Map());

  const getCanonicalKey = useCallback(
    (key: string): string | null => {
      if (uploadCacheRef.current.has(key)) {
        return key;
      }
      return aliasRef.current.get(key) ?? null;
    },
    [],
  );

  const getCachedEntry = useCallback(
    (key?: string | null) => {
      if (!key) return undefined;
      const canonical = getCanonicalKey(key);
      if (!canonical) return undefined;
      return uploadCacheRef.current.get(canonical);
    },
    [getCanonicalKey],
  );

  const chatBlocked = isUploading || uploadJobs.some((job) => job.status !== "ready");

  const hasCachedFileForJob = useCallback(
    (job: UploadJob) => Boolean(getCachedEntry(job.fileHash) ?? getCachedEntry(job.clientSignature)),
    [getCachedEntry],
  );

  const rememberFile = useCallback(
    (canonicalKey: string, file: File, fallbackSig: string) => {
      if (!canonicalKey) return;
      if (uploadCacheRef.current.size >= MAX_CACHED_FILES) {
        const first = uploadCacheRef.current.keys().next();
        if (!first.done) {
          const staleKey = first.value;
          const staleEntry = uploadCacheRef.current.get(staleKey);
          if (staleEntry) {
            staleEntry.aliases.forEach((alias) => {
              if (alias !== staleKey) {
                aliasRef.current.delete(alias);
              }
            });
          }
          uploadCacheRef.current.delete(staleKey);
        }
      }
      const aliasSet = new Set<string>([canonicalKey]);
      if (fallbackSig && fallbackSig !== canonicalKey) {
        aliasSet.add(fallbackSig);
        aliasRef.current.set(fallbackSig, canonicalKey);
      }
      uploadCacheRef.current.set(canonicalKey, {
        file,
        aliases: aliasSet,
        signature: canonicalKey,
        fallbackSignature: fallbackSig,
      });
    },
    [],
  );

  const linkAlias = useCallback((alias: string, entry?: CachedUploadEntry) => {
    if (!alias || !entry || alias === entry.signature) return;
    if (entry.aliases.has(alias)) return;
    entry.aliases.add(alias);
    aliasRef.current.set(alias, entry.signature);
  }, []);

  const forgetFile = useCallback(
    (key?: string | null) => {
      if (!key) return;
      const canonical = getCanonicalKey(key);
      if (!canonical) return;
      const entry = uploadCacheRef.current.get(canonical);
      if (!entry) return;
      uploadCacheRef.current.delete(canonical);
      entry.aliases.forEach((alias) => {
        if (alias !== canonical) {
          aliasRef.current.delete(alias);
        }
      });
    },
    [getCanonicalKey],
  );

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

  const fetchUploadStatus = useCallback(async () => {
    try {
      const response = await fetch("/api/labs/conversation/uploads", {
        method: "GET",
        credentials: "include",
      });
      if (!response.ok) {
        return;
      }
      const payload = await response.json();
      setUploadJobs((payload?.items || []) as UploadJob[]);
      if (typeof payload?.queueDepth === "number") {
        setQueueDepth(payload.queueDepth);
      }
      if (typeof payload?.limit === "number") {
        setQueueLimit(payload.limit);
      }
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    if (!sessionInfo?.sessionId) {
      return;
    }
    fetchUploadStatus();
    const intervalId = window.setInterval(() => {
      void fetchUploadStatus();
    }, 5000);
    return () => {
      window.clearInterval(intervalId);
    };
  }, [sessionInfo?.sessionId, fetchUploadStatus]);

  useEffect(() => {
    if (!sessionInfo?.sessionId) {
      return;
    }
    const socket = io(SOCKET_ENDPOINT ?? "/", {
      withCredentials: true,
    });
    socketRef.current = socket;
    const sessionRoom = sessionInfo.sessionId;
    socket.emit("join_ingest_room", { sessionId: sessionRoom });
    socket.on("ingest_update", (payload: UploadJob) => {
      if (!payload || !payload.id) return;
      setUploadJobs((prev) => {
        const next = prev.filter((job) => job.id !== payload.id);
        return [payload, ...next].slice(0, 50);
      });
    });
    socket.on("disconnect", () => {
      // fallback to polling already active
    });
    return () => {
      socket.disconnect();
      socketRef.current = null;
    };
  }, [sessionInfo?.sessionId]);

  useEffect(() => {
    uploadJobs.forEach((job) => {
      if (formatStatus(job.status) === "ready") {
        forgetFile(job.fileHash);
        forgetFile(job.clientSignature);
      } else if (job.fileHash && job.clientSignature) {
        const entry = getCachedEntry(job.clientSignature);
        if (entry) {
          linkAlias(job.fileHash, entry);
        }
      }
    });
  }, [uploadJobs, forgetFile, getCachedEntry, linkAlias]);

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
      const response = await setNameOnServer(storedName, { silent: true });
      setSessionInfo((prev) =>
        prev
          ? {
              ...prev,
              hasName: true,
              displayName: storedName,
            }
          : prev,
      );
      if (response.pendingMemories?.length) {
        setMessages((prev) => [...prev, ...buildReminderMessages(response.pendingMemories)]);
      }
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
      const data = (await response.json()) as SessionInfo & { error?: string };
      if (!response.ok) {
        throw new Error(data?.error || "Failed to initialize Conversation Lab session.");
      }
      setSessionInfo(data);
      const reminderMessages = buildReminderMessages(data.pendingMemories);

      const stored = loadStoredChatHistory();
      if (stored && stored.sessionId === data.sessionId && stored.history?.length) {
        const restoredHistory = [...stored.history];
        setMessages(reminderMessages.length ? [...restoredHistory, ...reminderMessages] : restoredHistory);
      } else {
        clearStoredChatHistory();
        const initialMessages: ChatMessage[] = [
          {
            id: generateId(),
            role: "assistant",
            text: data.greeting,
            timestamp: formatTimestamp(),
            senderName: data.assistantName ?? ASSISTANT_NAME,
          },
        ];
        setMessages(reminderMessages.length ? [...initialMessages, ...reminderMessages] : initialMessages);
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

  const buildReminderMessages = (entries?: MemoryReminder[]) => {
    if (!entries?.length) {
      return [];
    }
    return entries.map((entry) =>
      buildAssistantMessage(entry.text, {
        id: `memory-${entry.id}-${Math.random().toString(16).slice(2)}`,
        timestamp: formatIsoTimestamp(entry.createdAt),
      }),
    );
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
    if (chatBlocked) {
      setError("Chat is temporarily disabled while uploads are processing.");
      return;
    }
    if (!sessionInfo) return;
    const trimmed = draft.trim();
    if (!trimmed || isSending || isUploading) return;

    setDraft("");
    setIsSending(true);
    setError(null);

    if (needsName) {
      try {
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
        setMessages((prev) => {
          const base = [...prev, buildAssistantMessage(nameResponse.assistantReply)];
          if (nameResponse.pendingMemories?.length) {
            return [...base, ...buildReminderMessages(nameResponse.pendingMemories)];
          }
          return base;
        });
      } catch (err) {
        const message = err instanceof Error ? err.message : "Unable to store name.";
        setError(message);
      } finally {
        setIsSending(false);
      }
      return;
    }

    const userMessage: ChatMessage = {
      id: generateId(),
      role: "user",
      text: trimmed,
      timestamp: formatTimestamp(),
    };
    setMessages((prev) => [...prev, userMessage]);

    let placeholderId: string | undefined;

    try {
      placeholderId = showThinkingBubble();
      const chatResponse = await sendChat(trimmed);
      resolveAssistantMessage(chatResponse.reply, { placeholderId });
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
    if (chatBlocked) {
      event.preventDefault();
      return;
    }
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
        const fileHash = await hashFile(file);
        const fallbackSig = fallbackSignature(file);
        rememberFile(fileHash, file, fallbackSig);
        const uploadResult = await ingestFile(file, { signature: fileHash, fallbackSignature: fallbackSig });
        const items = (uploadResult?.items || []) as UploadEnqueueResult[];
        if (items.length === 0) {
          setMessages((prev) => [
            ...prev,
            buildAssistantMessage(`Queued ${file.name}. I'll process it shortly.`),
          ]);
        } else {
          items.forEach((info) => {
            setMessages((prev) => [
              ...prev,
              buildAssistantMessage(
                `Queued ${info.filename} (status: ${info.status}). I'll let you know when it's ready.`,
              ),
            ]);
          });
        }
        void fetchUploadStatus();
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

  const setNameOnServer = async (name: string, options?: { silent?: boolean }): Promise<NameResponse> => {
    const response = await fetch("/api/labs/conversation/name", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, message: name }),
    });
    const payload = (await response.json()) as {
      ok?: boolean;
      error?: string;
      displayName: string;
      assistantReply: string;
      assistantName: string;
      pendingMemories?: MemoryReminder[];
    };
    if (!response.ok || payload?.ok === false) {
      throw new Error(payload?.error || "Failed to store name.");
    }
    persistDisplayName(payload.displayName);
    return {
      ...(payload as {
        displayName: string;
        assistantReply: string;
        assistantName: string;
        pendingMemories?: MemoryReminder[];
      }),
      pendingMemories: (payload?.pendingMemories || []) as MemoryReminder[],
      silent: options?.silent ?? false,
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

  const ingestFile = async (
    file: File,
    traits?: {
      signature: string;
      fallbackSignature: string;
    },
  ) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("description", "Conversation Lab upload");
    if (traits) {
      formData.append("fileMetadata", JSON.stringify(traits));
    }

    const response = await fetch("/api/labs/conversation/ingest", {
      method: "POST",
      credentials: "include",
      body: formData,
    });

    const payload = await response.json();
    if (response.status === 202) {
      const queueDepth = payload?.queueDepth;
      const limit = payload?.limit;
      const detail =
        typeof queueDepth === "number" && typeof limit === "number"
          ? ` (${queueDepth}/${limit} pending)`
          : "";
      throw new Error((payload?.error || "Uploads are queued") + detail);
    }
    if (!response.ok || payload?.ok === false) {
      throw new Error(payload?.error || "Failed to process file");
    }
    return payload as { items: UploadEnqueueResult[]; count: number };
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

  const formatStatus = (status: string) => {
    if (!status) return "queued";
    const normalized = status.toLowerCase();
    if (normalized.startsWith("failed")) return "failed";
    return normalized;
  };

  const uploadStatusLabel = (status: string) => {
    const normalized = formatStatus(status);
    switch (normalized) {
      case "queued":
        return "Queued";
      case "processing":
        return "Processing";
      case "ready":
        return "Ready";
      case "failed":
        return "Failed";
      default:
        return status;
    }
  };

  const retryUpload = async (job: UploadJob) => {
    const entry = getCachedEntry(job.fileHash) ?? getCachedEntry(job.clientSignature);
    if (!entry) {
      setError("Original file isn’t available for retry. Please re-upload manually.");
      return;
    }
    const cached = entry.file;
    setRetryingJobId(job.id);
    try {
      await ingestFile(cached, { signature: entry.signature, fallbackSignature: entry.fallbackSignature });
      setMessages((prev) => [
        ...prev,
        buildAssistantMessage(`Retrying ${cached.name}. I’ll notify you when it finishes.`),
      ]);
      void fetchUploadStatus();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Retry failed.";
      setError(message);
      setMessages((prev) => [...prev, buildAssistantMessage(`Retry for ${cached.name} hit an error: ${message}`)]);
    } finally {
      setRetryingJobId(null);
    }
  };

  const describeStage = (stage?: string | null, detail?: string | null) => {
    if (!stage) return null;
    const normalized = stage.toLowerCase();
    switch (normalized) {
      case "processing":
        return detail || "Validating upload…";
      case "parsed":
        return detail || "Parsed file";
      case "translated":
        return "Translated to English";
      case "embedding":
        return detail || "Generating embeddings…";
      case "ready":
        return "Ready for queries";
      default:
        return detail || stage;
    }
  };

  const uploadsSection = () => {
    if (!uploadJobs.length) {
      return null;
    }
    return (
      <section className="clab-upload-status">
        <div className="clab-upload-header">
          <div>
            <p className="clab-upload-title">Uploaded files</p>
            <p className="clab-upload-subtitle">
              {queueDepth > 0
                ? `Processing… (${queueDepth} pending${queueLimit ? ` / limit ${queueLimit}` : ""})`
                : "All uploads are ready for RAG"}
            </p>
          </div>
        </div>
        <div className="clab-upload-list">
          {uploadJobs.map((job) => {
            const stageText = describeStage(job.progressStage, job.progressDetail);
            return (
              <div key={job.id} className={`clab-upload-card ${formatStatus(job.status)}`}>
                <div className="clab-upload-row">
                  <div>
                    <span className="clab-upload-name">{job.filename}</span>
                    <span className="clab-upload-type">{job.fileType?.toUpperCase()}</span>
                  </div>
                  <span className="clab-upload-pill">{uploadStatusLabel(job.status)}</span>
                </div>
                {stageText && <p className="clab-upload-stage">{stageText}</p>}
                {job.summary && formatStatus(job.status) === "ready" && (
                  <p className="clab-upload-summary">{job.summary}</p>
                )}
                {job.errorMessage && (
                  <p className="clab-upload-error">
                    {UPLOAD_ERROR_MESSAGES[job.errorCode ?? ""] ?? job.errorMessage}
                  </p>
                )}
                {formatStatus(job.status) === "failed" && hasCachedFileForJob(job) && (
                  <div className="clab-upload-actions">
                    <button
                      type="button"
                      onClick={() => void retryUpload(job)}
                      disabled={retryingJobId === job.id || isUploading}
                    >
                      {retryingJobId === job.id ? "Retrying..." : "Retry upload"}
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </section>
    );
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
                {chatBlocked
                  ? `Attach ${attachmentContext}. Chat is paused while uploads finish processing.`
                  : `Attach ${attachmentContext} or type a natural question. Responses stay inside this lab.`}
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

          {uploadsSection()}

          <div className="clab-chat-messages">
            {messages.map((message) => (
              <div key={message.id} className={`clab-message ${message.role} ${message.pending ? "pending" : ""}`}>
                <div className="clab-avatar" aria-hidden>
                  {message.role === "assistant"
                    ? "QA"
                    : (sessionInfo?.hasName && sessionInfo?.displayName ? sessionInfo.displayName : "You").slice(0, 2)}
                </div>
                <div className="clab-bubble">
                  <div className="clab-bubble-meta">
                    <span>
                      {message.role === "assistant"
                        ? ASSISTANT_NAME
                        : sessionInfo?.hasName && sessionInfo?.displayName
                          ? sessionInfo.displayName
                          : "You"}
                    </span>
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
                chatBlocked
                  ? "Chat paused while uploads finish."
                  : needsName
                    ? "First, let me know your name so I can personalize things."
                    : "Type a message..."
              }
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={handleKeyDown}
              disabled={chatBlocked || isSending || isUploading}
            />
            <button type="button" onClick={handleSend} disabled={chatBlocked || isSending || isUploading}>
              {chatBlocked ? "Wait for uploads" : needsName ? "Share name" : "Send"}
            </button>
          </div>
        </div>

      </section>
    </div>
  );
}
