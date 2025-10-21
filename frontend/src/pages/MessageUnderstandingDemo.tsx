import { useEffect, useMemo, useState } from "react";

type ChunkResult = {
  order: number;
  summary: string;
  text: string;
};

type PipelineStep = {
  label: string;
  detail: string;
};

type MessageResult = {
  id: string;
  finalSummary: string;
  chunks: ChunkResult[];
  steps: {
    detectedLanguage: string;
    sourceLanguage: string;
    targetLanguage: string;
    translationApplied: boolean;
    translationNote?: string | null;
    splitter: string;
    chunkCount: number;
    pipeline: PipelineStep[];
  };
};

const languageOptions = [
  { value: "en", label: "English" },
  { value: "es", label: "Spanish" },
  { value: "fr", label: "French" },
  { value: "de", label: "German" },
  { value: "zh", label: "Chinese" },
  { value: "auto", label: "Auto detect" },
];

export default function MessageUnderstandingDemo() {
  const [text, setText] = useState("");
  const [srcLang, setSrcLang] = useState<string>("auto");
  const [userLang, setUserLang] = useState<string>("en");
  const [mediaUrl, setMediaUrl] = useState<string>("");
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isDescribingImage, setIsDescribingImage] = useState(false);
  const [result, setResult] = useState<MessageResult | null>(null);
  const [imageCaption, setImageCaption] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [showChunks, setShowChunks] = useState<boolean>(true);
  const senderLanguage = useMemo(() => (srcLang === "auto" ? undefined : srcLang), [srcLang]);

  useEffect(() => {
    const previousTitle = document.title;
    document.title = "Message Lab";
    return () => {
      document.title = previousTitle;
    };
  }, []);

  useEffect(() => {
    setError("");
  }, [text, srcLang, userLang, imageFile, mediaUrl]);

  const handleProcess = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!text.trim()) {
      setError("Please enter a message to process.");
      return;
    }

    setIsProcessing(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch("/api/messages/process", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          text,
          srcLang: senderLanguage,
          userLang,
          mediaUrls: mediaUrl ? [mediaUrl] : undefined,
        }),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.error || "Failed to process message.");
      }

      const data = (await response.json()) as MessageResult;
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unexpected error.");
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDescribeImage = async () => {
    if (!imageFile && !mediaUrl) {
      setError("Please upload an image or provide an image URL.");
      return;
    }

    setIsDescribingImage(true);
    setError("");
    setImageCaption("");

    try {
      let payload: any = { userLang };
      if (mediaUrl) {
        payload.imageUrl = mediaUrl;
      } else if (imageFile) {
        const fileData = await fileToBase64(imageFile);
        payload.imageData = fileData;
      }

      const response = await fetch("/api/images/describe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.error || "Failed to describe image.");
      }

      const data = await response.json();
      setImageCaption(data.caption || "No description generated.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unexpected error while describing image.");
    } finally {
      setIsDescribingImage(false);
    }
  };

  return (
    <div className="labs-page section-padding">
      <header className="labs-header">
        <div>
          <h1>Message Lab</h1>
          <p>Simulate Quell-AI&apos;s safer splitting, translation, and summarization workflow.</p>
        </div>
        <div className="labs-actions">
          <button
            type="button"
            className={`button-outline ${showChunks ? "labs-toggle-active" : ""}`}
            onClick={() => setShowChunks((prev) => !prev)}
          >
            {showChunks ? "Hide Chunk Details" : "Show Chunk Details"}
          </button>
        </div>
      </header>

      <div className="labs-grid">
        <div className="labs-pane labs-pane-input">
          <form className="labs-form" onSubmit={handleProcess}>
            <label className="labs-label">
              Incoming message
              <textarea
                className="labs-textarea"
                placeholder="Paste a message, transcript, or voicemail..."
                value={text}
                onChange={(event) => setText(event.target.value)}
                rows={12}
              />
            </label>

            <div className="labs-row">
              <label className="labs-label">
                Sender language
                <select
                  className="labs-select"
                  value={srcLang}
                  onChange={(event) => setSrcLang(event.target.value)}
                >
                  {languageOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="labs-label">
                Your language
                <select
                  className="labs-select"
                  value={userLang}
                  onChange={(event) => setUserLang(event.target.value)}
                >
                  {languageOptions
                    .filter((option) => option.value !== "auto")
                    .map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                </select>
              </label>
            </div>

            <div className="labs-row labs-row-stack">
              <label className="labs-label">
                Image (optional)
                <input
                  type="file"
                  accept="image/*"
                  onChange={(event) => setImageFile(event.target.files ? event.target.files[0] : null)}
                  className="labs-file-input"
                />
              </label>
              <label className="labs-label">
                or Image URL
                <input
                  type="url"
                  placeholder="https://example.com/image.jpg"
                  className="labs-input"
                  value={mediaUrl}
                  onChange={(event) => setMediaUrl(event.target.value)}
                />
              </label>
            </div>

            {error && <p className="labs-error">{error}</p>}

            <div className="labs-button-row">
              <button type="submit" className="button-engage" disabled={isProcessing}>
                {isProcessing ? "Processing…" : "Send Message"}
              </button>
              <button
                type="button"
                className="button-outline"
                onClick={handleDescribeImage}
                disabled={isDescribingImage}
              >
                {isDescribingImage ? "Analyzing…" : "Describe Image"}
              </button>
            </div>
          </form>
        </div>

        <div className="labs-pane labs-pane-output">
          {result ? (
            <div className="labs-results">
              <section className="labs-card">
                <h2>Final Short Form</h2>
                <p className="labs-summary">{result.finalSummary}</p>
                <dl className="labs-steps">
                  <div>
                    <dt>Detected Language</dt>
                    <dd>{result.steps.detectedLanguage}</dd>
                  </div>
                  <div>
                    <dt>Translation</dt>
                    <dd>{result.steps.translationApplied ? result.steps.translationNote : "Not applied"}</dd>
                  </div>
                  <div>
                    <dt>Splitter</dt>
                    <dd>{result.steps.splitter} ({result.steps.chunkCount} chunks)</dd>
                  </div>
                </dl>
              </section>

              <section className="labs-card">
                <details className="labs-accordion" open>
                  <summary>Processing steps</summary>
                  <ol className="labs-pipeline">
                    {result.steps.pipeline.map((step, index) => (
                      <li key={step.label + index}>
                        <span className="labs-step-label">{step.label}</span>
                        <span className="labs-step-detail">{step.detail}</span>
                      </li>
                    ))}
                  </ol>
                </details>
              </section>

              {showChunks && (
                <section className="labs-card">
                  <h3>Per-chunk summaries</h3>
                  <div className="labs-chunk-list">
                    {result.chunks.map((chunk) => (
                      <article key={chunk.order} className="labs-chunk">
                        <header>
                          <span>Chunk {chunk.order + 1}</span>
                        </header>
                        <pre className="labs-chunk-summary">{chunk.summary}</pre>
                        <details>
                          <summary>View chunk text</summary>
                          <p>{chunk.text}</p>
                        </details>
                      </article>
                    ))}
                  </div>
                </section>
              )}
            </div>
          ) : (
            <div className="labs-empty-state">
              <h2>Awaiting input</h2>
              <p>Paste a long or multilingual message and Quell-AI will break it down into faithful, safer summaries.</p>
            </div>
          )}

          {imageCaption && (
            <section className="labs-card labs-image-card">
              <h3>Image understanding</h3>
              <p>{imageCaption}</p>
            </section>
          )}
        </div>
      </div>
    </div>
  );
}

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === "string") resolve(reader.result);
      else reject(new Error("Unable to read file"));
    };
    reader.onerror = () => reject(new Error("Unable to read file"));
    reader.readAsDataURL(file);
  });
}
