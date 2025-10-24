import { useEffect, useState, useRef } from "react";
import type { ChangeEvent } from "react";
import {
  uploadFile,
  submitText,
  validateFile,
  formatFileSize,
  getFileTypeLabel,
  type UploadProgress,
} from "../utils/documentUpload";

type DocumentRecord = {
  id: number;
  name: string;
  description?: string | null;
  classification?: string;
  sensitivity_level?: string;
  shareable?: boolean;
  allow_ai_to_suggest?: boolean;
  tags?: string[];
  allowed_recipients?: string[];
  allowed_contexts?: string[];
  blocked_contexts?: string[];
  last_shared_at?: string | null;
  file_type?: string;
  file_size_bytes?: number;
  content_metadata?: Record<string, any>;
  has_embedding?: boolean;
  version?: number;
  deleted_at?: string | null;
  created_at?: string;
};

type DocumentResponse = {
  documents: DocumentRecord[];
};

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Tab state
  const [activeTab, setActiveTab] = useState<"active" | "deleted">("active");

  // Upload state
  const [uploadMode, setUploadMode] = useState<"file" | "text" | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<UploadProgress | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);

  // Text input state
  const [textContent, setTextContent] = useState("");
  const [textName, setTextName] = useState("");
  const [textDescription, setTextDescription] = useState("");

  // File input state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [fileDescription, setFileDescription] = useState("");
  const [dragActive, setDragActive] = useState(false);
  
  // Deleted documents state
  const [deletedDocuments, setDeletedDocuments] = useState<DocumentRecord[]>([]);
  const [deletedLoading, setDeletedLoading] = useState(false);

  // Delete confirmation state
  const [deleteConfirm, setDeleteConfirm] = useState<{show: boolean; docId: number | null; docName: string}>({
    show: false,
    docId: null,
    docName: ""
  });
  const [deleteReason, setDeleteReason] = useState("");

  // Version history state
  const [versionHistory, setVersionHistory] = useState<{show: boolean; docId: number | null; versions: any[]}>({
    show: false,
    docId: null,
    versions: []
  });
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadDocuments();
  }, []);

  async function loadDocuments() {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("/api/documents", { credentials: "include" });
      if (!response.ok) {
        throw new Error(`request failed: ${response.status}`);
      }
      const payload = (await response.json()) as DocumentResponse;
      setDocuments(payload.documents);
    } catch (err) {
      setError(err instanceof Error ? err.message : "unknown error");
    } finally {
      setLoading(false);
    }
  }

  // File upload handlers
  function handleFileSelect(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file) {
      const validation = validateFile(file);
      if (!validation.valid) {
        setUploadError(validation.error || "Invalid file");
        return;
      }
      setSelectedFile(file);
      setUploadError(null);
    }
  }

  function handleDragOver(event: React.DragEvent) {
    event.preventDefault();
    setDragActive(true);
  }

  function handleDragLeave(event: React.DragEvent) {
    event.preventDefault();
    setDragActive(false);
  }

  function handleDrop(event: React.DragEvent) {
    event.preventDefault();
    setDragActive(false);
    
    const file = event.dataTransfer.files[0];
    if (file) {
      const validation = validateFile(file);
      if (!validation.valid) {
        setUploadError(validation.error || "Invalid file");
        return;
      }
      setSelectedFile(file);
      setUploadError(null);
    }
  }

  async function handleFileUpload() {
    if (!selectedFile) return;

    setUploading(true);
    setUploadError(null);
    setUploadSuccess(null);
    setUploadProgress(null);

    const result = await uploadFile(
      selectedFile,
      fileDescription,
      "internal",
      setUploadProgress
    );

    setUploading(false);

    if (result.success) {
      setUploadSuccess(`File "${selectedFile.name}" uploaded successfully!`);
      setSelectedFile(null);
      setFileDescription("");
      setUploadMode(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
      await loadDocuments();
      setTimeout(() => setUploadSuccess(null), 5000);
    } else {
      setUploadError(result.error || "Upload failed");
    }
  }

  async function handleTextSubmit() {
    if (!textContent.trim() || !textName.trim()) {
      setUploadError("Name and content are required");
      return;
    }

    setUploading(true);
    setUploadError(null);
    setUploadSuccess(null);

    const result = await submitText(
      textContent,
      textName,
      textDescription,
      "internal"
    );

    setUploading(false);

    if (result.success) {
      setUploadSuccess(`Text "${textName}" submitted successfully!`);
      setTextContent("");
      setTextName("");
      setTextDescription("");
      setUploadMode(null);
      await loadDocuments();
      setTimeout(() => setUploadSuccess(null), 5000);
    } else {
      setUploadError(result.error || "Submission failed");
    }
  }

  function cancelUpload() {
    setUploadMode(null);
    setSelectedFile(null);
    setFileDescription("");
    setTextContent("");
    setTextName("");
    setTextDescription("");
    setUploadError(null);
    setUploadProgress(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  // Load deleted documents
  async function loadDeletedDocuments() {
    setDeletedLoading(true);
    try {
      const response = await fetch("/api/documents/deleted", { credentials: "include" });
      if (!response.ok) throw new Error(`Failed to load deleted documents: ${response.status}`);
      const payload = await response.json();
      setDeletedDocuments(payload.documents || []);
    } catch (err) {
      console.error("Error loading deleted documents:", err);
    } finally {
      setDeletedLoading(false);
    }
  }

  // Show delete confirmation
  function showDeleteConfirmation(docId: number, docName: string) {
    setDeleteConfirm({ show: true, docId, docName });
    setDeleteReason("");
  }

  // Handle delete with reason
  async function confirmDelete() {
    if (!deleteConfirm.docId) return;

    try {
      const response = await fetch(
        `/api/documents/${deleteConfirm.docId}?reason=${encodeURIComponent(deleteReason)}`,
        {
          method: "DELETE",
          credentials: "include",
        }
      );

      if (!response.ok) throw new Error("Delete failed");

      setUploadSuccess(`Document "${deleteConfirm.docName}" deleted successfully`);
      setDeleteConfirm({ show: false, docId: null, docName: "" });
      setDeleteReason("");
      await loadDocuments();
      setTimeout(() => setUploadSuccess(null), 5000);
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "Delete failed");
    }
  }

  // Restore document
  async function restoreDocument(docId: number, docName: string) {
    try {
      const response = await fetch(`/api/documents/${docId}/restore`, {
        method: "POST",
        credentials: "include",
      });

      if (!response.ok) throw new Error("Restore failed");

      setUploadSuccess(`Document "${docName}" restored successfully`);
      await loadDocuments();
      await loadDeletedDocuments();
      setTimeout(() => setUploadSuccess(null), 5000);
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "Restore failed");
    }
  }

  // Load version history
  async function showVersionHistory(docId: number) {
    try {
      const response = await fetch(`/api/documents/${docId}/versions`, { credentials: "include" });
      if (!response.ok) throw new Error("Failed to load versions");
      const payload = await response.json();
      setVersionHistory({ show: true, docId, versions: payload.versions || [] });
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "Failed to load version history");
    }
  }

  // Handle tab change
  function handleTabChange(tab: "active" | "deleted") {
    setActiveTab(tab);
    if (tab === "deleted" && deletedDocuments.length === 0) {
      loadDeletedDocuments();
    }
  }

  return (
    <div className="section-padding">
      <div className="glass-panel" style={{ padding: "48px", marginBottom: "32px" }}>
        <h1 className="page-title">Document Guardrails & Data Feeds</h1>
        <p className="page-intro">
          Upload data feeds for AI processing and control which documents the AI can surface in meetings or chat. All uploads are processed with local OLLama for semantic search.
        </p>
      </div>

      {/* Upload Section */}
      <div className="glass-panel" style={{ padding: "32px", marginBottom: "32px" }}>
        <div className="panel-header">
          <h2 className="panel-title">Upload Data Feed</h2>
          <span className="panel-subtitle">Upload text files, CSV, or Excel data for AI semantic processing (max 100MB)</span>
        </div>

        {/* Success/Error Messages */}
        {uploadSuccess && (
          <div style={{ padding: "12px", marginBottom: "16px", background: "#d4edda", color: "#155724", borderRadius: "8px" }}>
            {uploadSuccess}
          </div>
        )}
        {uploadError && (
          <div style={{ padding: "12px", marginBottom: "16px", background: "#f8d7da", color: "#721c24", borderRadius: "8px" }}>
            {uploadError}
          </div>
        )}

        {!uploadMode && (
          <div style={{ display: "flex", gap: "16px" }}>
            <button
              className="btn btn-primary"
              onClick={() => setUploadMode("file")}
              style={{ padding: "12px 24px" }}
            >
              📁 Upload File
            </button>
            <button
              className="btn btn-secondary"
              onClick={() => setUploadMode("text")}
              style={{ padding: "12px 24px" }}
            >
              📝 Enter Text
            </button>
          </div>
        )}

        {/* File Upload Mode */}
        {uploadMode === "file" && (
          <div style={{ marginTop: "16px" }}>
            <div
              style={{
                border: dragActive ? "2px dashed #007bff" : "2px dashed #ccc",
                borderRadius: "8px",
                padding: "32px",
                textAlign: "center",
                background: dragActive ? "#f0f8ff" : "#f9f9f9",
                cursor: "pointer",
              }}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".txt,.csv,.xlsx,.json"
                  onChange={handleFileSelect}
                  style={{ display: "none" }}
                />
              {!selectedFile && (
                <>
                  <p style={{ fontSize: "18px", marginBottom: "8px" }}>📤 Drag and drop file here or click to browse</p>
                  <p style={{ fontSize: "14px", color: "#666" }}>Supported: .txt, .csv, .xlsx, .json (max 100MB)</p>
                </>
              )}
              {selectedFile && (
                <div>
                  <p style={{ fontSize: "16px", fontWeight: "bold", marginBottom: "8px" }}>
                    ✅ {selectedFile.name}
                  </p>
                  <p style={{ fontSize: "14px", color: "#666" }}>
                    {formatFileSize(selectedFile.size)} • {getFileTypeLabel(selectedFile.name.split('.').pop())}
                  </p>
                </div>
              )}
            </div>

            {selectedFile && (
              <div style={{ marginTop: "16px" }}>
                <label style={{ display: "block", marginBottom: "8px", fontWeight: "500" }}>
                  Description (optional):
                </label>
                <textarea
                  value={fileDescription}
                  onChange={(e) => setFileDescription(e.target.value)}
                  placeholder="Enter a description for this file..."
                  rows={3}
                  style={{
                    width: "100%",
                    padding: "12px",
                    borderRadius: "8px",
                    border: "1px solid #ccc",
                    fontFamily: "inherit",
                  }}
                />
              </div>
            )}

            {uploadProgress && (
              <div style={{ marginTop: "16px" }}>
                <div style={{ marginBottom: "8px", display: "flex", justifyContent: "space-between" }}>
                  <span>Uploading...</span>
                  <span>{uploadProgress.percentage}%</span>
                </div>
                <div style={{ height: "8px", background: "#e0e0e0", borderRadius: "4px", overflow: "hidden" }}>
                  <div
                    style={{
                      height: "100%",
                      background: "#007bff",
                      width: `${uploadProgress.percentage}%`,
                      transition: "width 0.3s",
                    }}
                  />
                </div>
              </div>
            )}

            <div style={{ marginTop: "16px", display: "flex", gap: "12px" }}>
              <button
                className="btn btn-primary"
                onClick={handleFileUpload}
                disabled={!selectedFile || uploading}
                style={{ padding: "10px 24px" }}
              >
                {uploading ? "Uploading..." : "Upload"}
              </button>
              <button
                className="btn btn-secondary"
                onClick={cancelUpload}
                disabled={uploading}
                style={{ padding: "10px 24px" }}
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Text Input Mode */}
        {uploadMode === "text" && (
          <div style={{ marginTop: "16px" }}>
            <div style={{ marginBottom: "16px" }}>
              <label style={{ display: "block", marginBottom: "8px", fontWeight: "500" }}>
                Name: *
              </label>
              <input
                type="text"
                value={textName}
                onChange={(e) => setTextName(e.target.value)}
                placeholder="Enter a name for this text input..."
                style={{
                  width: "100%",
                  padding: "12px",
                  borderRadius: "8px",
                  border: "1px solid #ccc",
                  fontFamily: "inherit",
                }}
              />
            </div>

            <div style={{ marginBottom: "16px" }}>
              <label style={{ display: "block", marginBottom: "8px", fontWeight: "500" }}>
                Content: *
              </label>
              <textarea
                value={textContent}
                onChange={(e) => setTextContent(e.target.value)}
                placeholder="Enter or paste your text content here..."
                rows={10}
                style={{
                  width: "100%",
                  padding: "12px",
                  borderRadius: "8px",
                  border: "1px solid #ccc",
                  fontFamily: "inherit",
                }}
              />
              <p style={{ fontSize: "12px", color: "#666", marginTop: "4px" }}>
                {textContent.length} characters
              </p>
            </div>

            <div style={{ marginBottom: "16px" }}>
              <label style={{ display: "block", marginBottom: "8px", fontWeight: "500" }}>
                Description (optional):
              </label>
              <textarea
                value={textDescription}
                onChange={(e) => setTextDescription(e.target.value)}
                placeholder="Enter a description..."
                rows={3}
                style={{
                  width: "100%",
                  padding: "12px",
                  borderRadius: "8px",
                  border: "1px solid #ccc",
                  fontFamily: "inherit",
                }}
              />
            </div>

            <div style={{ display: "flex", gap: "12px" }}>
              <button
                className="btn btn-primary"
                onClick={handleTextSubmit}
                disabled={!textContent.trim() || !textName.trim() || uploading}
                style={{ padding: "10px 24px" }}
              >
                {uploading ? "Submitting..." : "Submit"}
              </button>
              <button
                className="btn btn-secondary"
                onClick={cancelUpload}
                disabled={uploading}
                style={{ padding: "10px 24px" }}
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="glass-panel" style={{ padding: "32px", marginBottom: "32px" }}>
        <h2 className="panel-title">Policy snapshot</h2>
        <div className="bullet-columns">
          <div>
            <h3 className="bullet-heading">Sharing heuristics</h3>
            <ul className="bullet-list">
              <li>Auto-share only with verified attendees or internal domains.</li>
              <li>Context tags (for example, "budget review") map instructions to files.</li>
              <li>One-click revoke stops AI usage but keeps audit logs.</li>
            </ul>
          </div>
          <div>
            <h3 className="bullet-heading">Audit highlights</h3>
            <ul className="bullet-list">
              <li>Every share is logged with session metadata for audits.</li>
              <li>Voice disclosure and document policy rely on the same toggle.</li>
              <li>Retention timers clean up sensitive assets automatically.</li>
            </ul>
          </div>
        </div>
      </div>

      <div className="glass-panel" style={{ padding: "32px" }}>
        <div className="panel-header">
          <h2 className="panel-title">Managed documents</h2>
          <span className="panel-subtitle">Define the approved corpus the AI can reference or share.</span>
        </div>

        {/* Tabs */}
        <div style={{ display: "flex", gap: "16px", marginBottom: "24px", borderBottom: "1px solid #ddd" }}>
          <button
            onClick={() => handleTabChange("active")}
            style={{
              padding: "12px 24px",
              background: "none",
              border: "none",
              borderBottom: activeTab === "active" ? "2px solid #007bff" : "none",
              color: activeTab === "active" ? "#007bff" : "#666",
              cursor: "pointer",
              fontWeight: activeTab === "active" ? "bold" : "normal",
            }}
          >
            Active Documents
          </button>
          <button
            onClick={() => handleTabChange("deleted")}
            style={{
              padding: "12px 24px",
              background: "none",
              border: "none",
              borderBottom: activeTab === "deleted" ? "2px solid #007bff" : "none",
              color: activeTab === "deleted" ? "#007bff" : "#666",
              cursor: "pointer",
              fontWeight: activeTab === "deleted" ? "bold" : "normal",
            }}
          >
            Deleted Documents
          </button>
        </div>

        {/* Active Documents Tab */}
        {activeTab === "active" && (
          <>
            {loading && <p>Loading documents...</p>}
            {!loading && error && <p role="alert">{error}</p>}
            {!loading && !error && documents.length === 0 && (
              <p>No documents saved yet. Upload a briefing pack or link a shared drive item to start.</p>
            )}
            {!loading && !error && documents.length > 0 && (
              <div className="table" role="table">
                <div className="table-row table-header" role="row">
                  <span role="columnheader">Name</span>
                  <span role="columnheader">Type</span>
                  <span role="columnheader">Size</span>
                  <span role="columnheader">Version</span>
                  <span role="columnheader">AI Processed</span>
                  <span role="columnheader">Actions</span>
                </div>
                {documents.map((doc) => (
                  <div key={doc.id} className="table-row" role="row">
                    <span role="cell" title={doc.description || doc.name}>
                      {doc.name}
                    </span>
                    <span role="cell">{getFileTypeLabel(doc.file_type)}</span>
                    <span role="cell">{formatFileSize(doc.file_size_bytes)}</span>
                    <span role="cell">
                      v{doc.version || 1}
                      {doc.version && doc.version > 1 && (
                        <button
                          onClick={() => showVersionHistory(doc.id)}
                          style={{
                            marginLeft: "8px",
                            padding: "2px 8px",
                            fontSize: "12px",
                            cursor: "pointer",
                          }}
                        >
                          History
                        </button>
                      )}
                    </span>
                    <span role="cell">{doc.has_embedding ? "✅ Yes" : "⏳ Pending"}</span>
                    <span role="cell">
                      <button
                        onClick={() => showDeleteConfirmation(doc.id, doc.name)}
                        style={{
                          padding: "4px 12px",
                          background: "#dc3545",
                          color: "white",
                          border: "none",
                          borderRadius: "4px",
                          cursor: "pointer",
                        }}
                      >
                        Delete
                      </button>
                    </span>
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {/* Deleted Documents Tab */}
        {activeTab === "deleted" && (
          <>
            {deletedLoading && <p>Loading deleted documents...</p>}
            {!deletedLoading && deletedDocuments.length === 0 && (
              <p>No deleted documents.</p>
            )}
            {!deletedLoading && deletedDocuments.length > 0 && (
              <div className="table" role="table">
                <div className="table-row table-header" role="row">
                  <span role="columnheader">Name</span>
                  <span role="columnheader">Type</span>
                  <span role="columnheader">Deleted At</span>
                  <span role="columnheader">Actions</span>
                </div>
                {deletedDocuments.map((doc) => (
                  <div key={doc.id} className="table-row" role="row">
                    <span role="cell">{doc.name}</span>
                    <span role="cell">{getFileTypeLabel(doc.file_type)}</span>
                    <span role="cell">
                      {doc.deleted_at ? new Date(doc.deleted_at).toLocaleDateString() : "Unknown"}
                    </span>
                    <span role="cell">
                      <button
                        onClick={() => restoreDocument(doc.id, doc.name)}
                        style={{
                          padding: "4px 12px",
                          background: "#28a745",
                          color: "white",
                          border: "none",
                          borderRadius: "4px",
                          cursor: "pointer",
                        }}
                      >
                        Restore
                      </button>
                    </span>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      {deleteConfirm.show && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0, 0, 0, 0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
          }}
          onClick={() => setDeleteConfirm({ show: false, docId: null, docName: "" })}
        >
          <div
            style={{
              background: "white",
              padding: "32px",
              borderRadius: "8px",
              maxWidth: "500px",
              width: "90%",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3 style={{ marginTop: 0 }}>Delete Document</h3>
            <p>Are you sure you want to delete "{deleteConfirm.docName}"?</p>
            <p style={{ fontSize: "14px", color: "#666" }}>
              The document will be hidden but data preserved for audit purposes.
            </p>
            <div style={{ marginBottom: "16px" }}>
              <label style={{ display: "block", marginBottom: "8px" }}>
                Reason (optional):
              </label>
              <input
                type="text"
                value={deleteReason}
                onChange={(e) => setDeleteReason(e.target.value)}
                placeholder="Enter reason for deletion..."
                style={{
                  width: "100%",
                  padding: "8px",
                  borderRadius: "4px",
                  border: "1px solid #ccc",
                }}
              />
            </div>
            <div style={{ display: "flex", gap: "12px", justifyContent: "flex-end" }}>
              <button
                onClick={() => setDeleteConfirm({ show: false, docId: null, docName: "" })}
                style={{ padding: "8px 16px" }}
              >
                Cancel
              </button>
              <button
                onClick={confirmDelete}
                style={{
                  padding: "8px 16px",
                  background: "#dc3545",
                  color: "white",
                  border: "none",
                  borderRadius: "4px",
                  cursor: "pointer",
                }}
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Version History Modal */}
      {versionHistory.show && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0, 0, 0, 0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
          }}
          onClick={() => setVersionHistory({ show: false, docId: null, versions: [] })}
        >
          <div
            style={{
              background: "white",
              padding: "32px",
              borderRadius: "8px",
              maxWidth: "600px",
              width: "90%",
              maxHeight: "80vh",
              overflow: "auto",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3 style={{ marginTop: 0 }}>Version History</h3>
            {versionHistory.versions.length === 0 && <p>No version history available.</p>}
            {versionHistory.versions.length > 0 && (
              <div>
                {versionHistory.versions.map((v) => (
                  <div
                    key={v.version}
                    style={{
                      padding: "12px",
                      marginBottom: "12px",
                      border: "1px solid #ddd",
                      borderRadius: "4px",
                    }}
                  >
                    <div style={{ fontWeight: "bold" }}>Version {v.version}</div>
                    <div style={{ fontSize: "14px", color: "#666" }}>
                      {v.created_at ? new Date(v.created_at).toLocaleString() : "Unknown date"}
                    </div>
                  </div>
                ))}
              </div>
            )}
            <button
              onClick={() => setVersionHistory({ show: false, docId: null, versions: [] })}
              style={{ padding: "8px 16px", marginTop: "16px" }}
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
