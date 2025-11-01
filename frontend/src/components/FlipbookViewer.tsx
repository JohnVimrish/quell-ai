import { useEffect, useMemo, useRef, useState, type CSSProperties } from "react";
import { init as initFlipbook } from "flipbook-viewer";
import { GlobalWorkerOptions, getDocument, type PDFDocumentProxy } from "pdfjs-dist";
import pdfjsWorker from "pdfjs-dist/build/pdf.worker?url";

import type { FlipbookViewerInstance } from "flipbook-viewer";

GlobalWorkerOptions.workerSrc = pdfjsWorker;

type FlipbookViewerStatus = "idle" | "loading" | "ready" | "error";

type FlipbookViewerProps = {
  pdfUrl: string;
  className?: string;
  maxWidth?: number;
  aspectRatio?: number;
  onLoading?: () => void;
  onReady?: () => void;
  onError?: (error: Error) => void;
};

type CachedPage = {
  img: HTMLImageElement;
  num: number;
  width: number;
  height: number;
};

type PdfLoadingTask = ReturnType<typeof getDocument>;

const DEFAULT_MAX_WIDTH = 1080;
const DEFAULT_ASPECT_RATIO = 0.68;

function cx(...parts: Array<string | false | null | undefined>) {
  return parts.filter(Boolean).join(" ");
}

function normalizeError(value: unknown): Error {
  if (value instanceof Error) return value;
  if (typeof value === "string") return new Error(value);

  try {
    return new Error(JSON.stringify(value));
  } catch {
    return new Error("An unknown error occurred while loading the flipbook.");
  }
}

function clearInteractiveHandlers(element: HTMLElement | null) {
  if (!element) return;

  element.onmouseenter = null;
  element.onmouseleave = null;
  element.onmousemove = null;
  element.onclick = null;
  element.onmousedown = null;
  element.onmouseup = null;
}

export default function FlipbookViewer({
  pdfUrl,
  className,
  maxWidth = DEFAULT_MAX_WIDTH,
  aspectRatio = DEFAULT_ASPECT_RATIO,
  onLoading,
  onReady,
  onError,
}: FlipbookViewerProps) {
  const wrapperRef = useRef<HTMLDivElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const viewerRef = useRef<FlipbookViewerInstance | null>(null);
  const loadingTaskRef = useRef<PdfLoadingTask | null>(null);
  const cleanupRef = useRef<(() => void) | null>(null);
  const callbacksRef = useRef<{
    onLoading?: () => void;
    onReady?: () => void;
    onError?: (error: Error) => void;
  }>({
    onLoading,
    onReady,
    onError,
  });

  const [status, setStatus] = useState<FlipbookViewerStatus>("idle");
  const [measuredWidth, setMeasuredWidth] = useState<number>(maxWidth);
  const [currentPageIndex, setCurrentPageIndex] = useState(0);
  const [totalPages, setTotalPages] = useState(0);

  useEffect(() => {
    callbacksRef.current = {
      onLoading,
      onReady,
      onError,
    };
  }, [onLoading, onReady, onError]);

  useEffect(() => {
    const host = wrapperRef.current;
    if (!host) return;

    const updateWidth = (width: number) => {
      const rounded = Math.round(width);
      setMeasuredWidth((prev) => {
        if (!prev || Math.abs(prev - rounded) > 1) {
          return rounded;
        }
        return prev;
      });
    };

    updateWidth(host.clientWidth || maxWidth);

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        updateWidth(entry.contentRect.width);
      }
    });

    observer.observe(host);
    return () => observer.disconnect();
  }, [maxWidth]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || measuredWidth <= 0) {
      return;
    }

    let cancelled = false;
    let pdfDoc: PDFDocumentProxy | null = null;
    const cache = new Map<number, CachedPage>();

    const targetWidth = Math.min(measuredWidth, maxWidth);
    const targetHeight = Math.round(targetWidth * aspectRatio);

    clearInteractiveHandlers(container);
    container.innerHTML = "";
    container.style.maxWidth = `${Math.round(maxWidth)}px`;
    container.style.minHeight = `${targetHeight}px`;

    loadingTaskRef.current?.destroy().catch(() => undefined);
    loadingTaskRef.current = null;

    setStatus("loading");
    callbacksRef.current.onLoading?.();

    const loadingTask = getDocument(pdfUrl);
    loadingTaskRef.current = loadingTask;

    const handleFatalError = (error: unknown) => {
      if (cancelled) {
        return;
      }
      const normalized = normalizeError(error);
      setStatus("error");
      callbacksRef.current.onError?.(normalized);
      console.error("[FlipbookViewer] Initialization failed:", normalized);
    };

    loadingTask.promise
      .then((pdf) => {
        if (cancelled) {
          return;
        }

        pdfDoc = pdf;

        const loadPage = (pageNumber: number, cb: (err?: unknown, page?: CachedPage) => void) => {
          if (!pdfDoc) {
            cb(new Error("PDF document has not finished loading."));
            return;
          }

          if (!pageNumber || pageNumber > pdfDoc.numPages) {
            cb(null);
            return;
          }

          const cached = cache.get(pageNumber);
          if (cached) {
            cb(null, cached);
            return;
          }

          pdfDoc
            .getPage(pageNumber)
            .then((page) => {
              if (cancelled) {
                cb();
                return;
              }

              const viewport = page.getViewport({ scale: 1.25 });
              const outputScale = window.devicePixelRatio || 1;

              const canvas = document.createElement("canvas");
              const context = canvas.getContext("2d");

              if (!context) {
                cb(new Error("Unable to acquire a 2D canvas context for the PDF page render."));
                return;
              }

              canvas.width = Math.floor(viewport.width * outputScale);
              canvas.height = Math.floor(viewport.height * outputScale);
              canvas.style.width = `${Math.floor(viewport.width)}px`;
              canvas.style.height = `${Math.floor(viewport.height)}px`;

              const transform = outputScale !== 1 ? [outputScale, 0, 0, outputScale, 0, 0] : undefined;

              const renderTask = page.render({
                canvasContext: context,
                viewport,
                transform,
                canvas,
              });

              renderTask.promise
                .then(() => {
                  if (cancelled) {
                    cb();
                    return;
                  }

                  const img = new Image();
                  img.src = canvas.toDataURL("image/png");

                  const finalize = () => {
                    if (cancelled) {
                      cb();
                      return;
                    }

                    const asset: CachedPage = {
                      img,
                      num: pageNumber,
                      width: img.width,
                      height: img.height,
                    };
                    cache.set(pageNumber, asset);
                    cb(null, asset);
                  };

                  if (img.complete) {
                    finalize();
                  } else {
                    img.addEventListener("load", finalize, { once: true });
                    img.addEventListener(
                      "error",
                      () => cb(new Error(`Failed to load rendered image for page ${pageNumber}.`)),
                      { once: true },
                    );
                  }
                })
                .catch((renderErr) => {
                  console.error(`[FlipbookViewer] Rendering error on page ${pageNumber}:`, renderErr);
                  cb(renderErr);
                });
            })
            .catch((pageErr) => {
              console.error(`[FlipbookViewer] Failed to retrieve page ${pageNumber}:`, pageErr);
              cb(pageErr);
            });
        };

        const book = {
          numPages: () => pdfDoc?.numPages ?? 0,
          getPage: (pageNumber: number, cb: (err?: unknown, page?: CachedPage) => void) => loadPage(pageNumber, cb),
        };

        const opts = {
          backgroundColor: "rgba(248, 248, 248, 0.92)",
          boxBorder: 0,
          width: targetWidth,
          height: targetHeight,
          marginTop: 6,
          marginLeft: 6,
        };

        initFlipbook(book, container, opts, (err, viewer) => {
          if (cancelled) {
            return;
          }

          if (err) {
            handleFatalError(err);
            return;
          }

          viewerRef.current = viewer ?? null;
          setTotalPages(viewer?.page_count ?? 0);
          setCurrentPageIndex(0);

          if (viewer && typeof viewer.on === "function") {
            const handleSeen = (pageIndex: unknown) => {
              if (cancelled) return;
              if (typeof pageIndex === "number") {
                setCurrentPageIndex(pageIndex);
              }
            };

            viewer.on("seen", handleSeen);

            const cleanupSeen = () => {
              if (!viewer) return;
              if (typeof viewer.off === "function") {
                viewer.off("seen", handleSeen);
              } else if (typeof (viewer as any).removeListener === "function") {
                (viewer as any).removeListener("seen", handleSeen);
              }
            };

            cleanupRef.current?.();
            cleanupRef.current = cleanupSeen;
          }

          setStatus("ready");
          callbacksRef.current.onReady?.();

          const preloadLimit = Math.min(book.numPages(), 6);
          for (let pageNumber = 1; pageNumber <= preloadLimit; pageNumber += 1) {
            loadPage(pageNumber, () => undefined);
          }
        });
      })
      .catch((error) => handleFatalError(error));

    return () => {
      cancelled = true;
      clearInteractiveHandlers(container);
      container.innerHTML = "";

      loadingTaskRef.current?.destroy().catch(() => undefined);
      loadingTaskRef.current = null;
      viewerRef.current = null;
      cleanupRef.current?.();
      cleanupRef.current = null;
      setTotalPages(0);
      setCurrentPageIndex(0);
      cache.clear();
      pdfDoc = null;
    };
  }, [pdfUrl, measuredWidth, maxWidth, aspectRatio]);

  const computedWidth = Math.min(measuredWidth || maxWidth, maxWidth);
  const computedHeight = Math.round(computedWidth * aspectRatio);
  const totalSpreads = useMemo(() => Math.max(1, Math.ceil(totalPages / 2)), [totalPages]);
  const currentSpread = useMemo(
    () => Math.min(totalSpreads, Math.max(1, Math.floor(currentPageIndex / 2) + 1)),
    [currentPageIndex, totalSpreads],
  );

  const showOpeningBlend = status === "ready" && currentSpread === 1;
  const baseBackdropStyle = useMemo<CSSProperties>(
    () =>
      showOpeningBlend
        ? {
            background:
              "linear-gradient(90deg, rgba(248,248,248,0) 0%, rgba(248,248,248,0.72) 45%, rgba(248,248,248,0.92) 100%)",
          }
        : {
            background: "rgba(248,248,248,0.92)",
          },
    [showOpeningBlend],
  );

  const openingBlendStyle = useMemo<CSSProperties>(
    () => ({
      background: "linear-gradient(90deg, rgba(248,248,248,0.88) 0%, rgba(248,248,248,0.45) 100%)",
      mixBlendMode: "multiply" as CSSProperties["mixBlendMode"],
    }),
    [],
  );

  const canFlipForward = currentSpread < totalSpreads;
  const canFlipBackward = currentSpread > 1;

  const handleFlipForward = () => {
    const viewer = viewerRef.current;
    if (!viewer || !canFlipForward) return;
    viewer.flip_forward();
  };

  const handleFlipBackward = () => {
    const viewer = viewerRef.current;
    if (!viewer || !canFlipBackward) return;
    viewer.flip_back();
  };

  return (
    <div
      ref={wrapperRef}
      className={cx("w-full", className)}
      style={{ minHeight: `${computedHeight}px` }}
      data-status={status}
    >
      <div
        className="relative mx-auto"
        style={{
          width: "100%",
          maxWidth: `${Math.round(maxWidth)}px`,
          minHeight: `${computedHeight}px`,
        }}
      >
        <div
          className="pointer-events-none absolute inset-0 z-0 rounded-[36px] border border-border-grey/40 shadow-xl shadow-primary-blue/10 transition-all duration-700 ease-out"
          style={{
            ...baseBackdropStyle,
            minHeight: `${computedHeight}px`,
          }}
          aria-hidden="true"
        />

        {showOpeningBlend && (
          <div
            className="pointer-events-none absolute inset-y-8 left-0 z-10 w-[52%] rounded-l-[30px]"
            style={openingBlendStyle}
            aria-hidden="true"
          />
        )}

        <div
          ref={containerRef}
          className="relative z-20 transition-opacity duration-500 ease-out"
          style={{
            width: "100%",
            minHeight: `${computedHeight}px`,
            opacity: status === "ready" ? 1 : 0,
            pointerEvents: status === "ready" ? "auto" : "none",
          }}
          aria-live="polite"
          aria-busy={status !== "ready"}
        />

        {status === "ready" && (
          <div className="pointer-events-none absolute inset-0 z-30 flex items-center justify-between px-4">
            <button
              type="button"
              onClick={handleFlipBackward}
              aria-label="Previous spread"
              disabled={!canFlipBackward}
              className={cx(
                "pointer-events-auto inline-flex h-12 w-12 items-center justify-center rounded-full border border-border-grey/60 bg-white/85 text-primary-blue shadow-lg shadow-primary-blue/25 transition-all hover:scale-105 hover:bg-primary-blue hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-blue/50",
                !canFlipBackward && "opacity-40 hover:scale-100 hover:bg-white",
              )}
            >
              <span aria-hidden="true" className="text-xl font-semibold">
                {"‹"}
              </span>
            </button>

            <div className="pointer-events-none absolute bottom-6 left-1/2 -translate-x-1/2 rounded-full border border-border-grey/60 bg-white/85 px-5 py-1.5 text-xs font-semibold uppercase tracking-[0.2em] text-light-text shadow-md shadow-primary-blue/15">
              Spread {currentSpread} / {totalSpreads}
            </div>

            <button
              type="button"
              onClick={handleFlipForward}
              aria-label="Next spread"
              disabled={!canFlipForward}
              className={cx(
                "pointer-events-auto inline-flex h-12 w-12 items-center justify-center rounded-full border border-border-grey/60 bg-white/85 text-primary-blue shadow-lg shadow-primary-blue/25 transition-all hover:scale-105 hover:bg-primary-blue hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-blue/50",
                !canFlipForward && "opacity-40 hover:scale-100 hover:bg-white",
              )}
            >
              <span aria-hidden="true" className="text-xl font-semibold">
                {"›"}
              </span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
