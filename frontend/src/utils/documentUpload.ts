/**
 * Document upload utilities for data feeds
 */

const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100 MB
const ALLOWED_EXTENSIONS = ['txt', 'csv', 'xlsx'];

export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

export interface DocumentRecord {
  id: number;
  name: string;
  description?: string;
  file_type?: string;
  file_size_bytes?: number;
  content_metadata?: Record<string, any>;
  vector_metadata?: Record<string, any>;
  created_at?: string;
  has_embedding?: boolean;
}

export interface UploadResult {
  success: boolean;
  document?: DocumentRecord;
  error?: string;
}

export interface TextSubmitResult {
  success: boolean;
  document?: DocumentRecord;
  error?: string;
}

/**
 * Validate file before upload
 */
export function validateFile(file: File): { valid: boolean; error?: string } {
  // Check file size
  if (file.size > MAX_FILE_SIZE) {
    const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
    return {
      valid: false,
      error: `File size (${sizeMB} MB) exceeds the 100 MB limit. Please upload larger files to the designated SharePoint location.`,
    };
  }

  // Check file extension
  const extension = file.name.split('.').pop()?.toLowerCase();
  if (!extension || !ALLOWED_EXTENSIONS.includes(extension)) {
    return {
      valid: false,
      error: `File type not allowed. Supported types: ${ALLOWED_EXTENSIONS.join(', ')}`,
    };
  }

  return { valid: true };
}

/**
 * Upload a file as a data feed
 */
export async function uploadFile(
  file: File,
  description?: string,
  classification?: string,
  onProgress?: (progress: UploadProgress) => void
): Promise<UploadResult> {
  // Validate file
  const validation = validateFile(file);
  if (!validation.valid) {
    return {
      success: false,
      error: validation.error,
    };
  }

  try {
    // Create form data
    const formData = new FormData();
    formData.append('file', file);
    if (description) {
      formData.append('description', description);
    }
    if (classification) {
      formData.append('classification', classification);
    }

    // Create XHR for progress tracking
    const xhr = new XMLHttpRequest();

    // Setup progress handler
    if (onProgress) {
      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable) {
          onProgress({
            loaded: event.loaded,
            total: event.total,
            percentage: Math.round((event.loaded / event.total) * 100),
          });
        }
      });
    }

    // Create promise for the upload
    const uploadPromise = new Promise<DocumentRecord>((resolve, reject) => {
      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          const response = JSON.parse(xhr.responseText);
          resolve(response);
        } else {
          try {
            const error = JSON.parse(xhr.responseText);
            reject(new Error(error.error || 'Upload failed'));
          } catch {
            reject(new Error(`Upload failed with status ${xhr.status}`));
          }
        }
      });

      xhr.addEventListener('error', () => {
        reject(new Error('Network error during upload'));
      });

      xhr.addEventListener('abort', () => {
        reject(new Error('Upload aborted'));
      });

      xhr.open('POST', '/api/documents/upload');
      xhr.withCredentials = true;
      xhr.send(formData);
    });

    const document = await uploadPromise;
    return {
      success: true,
      document,
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred',
    };
  }
}

/**
 * Submit text as a data feed
 */
export async function submitText(
  content: string,
  name: string,
  description?: string,
  classification?: string
): Promise<TextSubmitResult> {
  if (!content || !content.trim()) {
    return {
      success: false,
      error: 'Content cannot be empty',
    };
  }

  if (!name || !name.trim()) {
    return {
      success: false,
      error: 'Name is required',
    };
  }

  try {
    const response = await fetch('/api/documents/text', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({
        content,
        name,
        description,
        classification,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      return {
        success: false,
        error: error.error || 'Submission failed',
      };
    }

    const document = await response.json();
    return {
      success: true,
      document,
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred',
    };
  }
}

/**
 * Fetch document content
 */
export async function fetchDocumentContent(documentId: number): Promise<{
  success: boolean;
  content?: any;
  error?: string;
}> {
  try {
    const response = await fetch(`/api/documents/${documentId}/content`, {
      credentials: 'include',
    });

    if (!response.ok) {
      const error = await response.json();
      return {
        success: false,
        error: error.error || 'Failed to fetch content',
      };
    }

    const content = await response.json();
    return {
      success: true,
      content,
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred',
    };
  }
}

/**
 * Format file size for display
 */
export function formatFileSize(bytes?: number): string {
  if (!bytes) return 'Unknown';
  
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

/**
 * Get file type icon/label
 */
export function getFileTypeLabel(fileType?: string): string {
  switch (fileType?.toLowerCase()) {
    case 'txt':
      return 'Text File';
    case 'csv':
      return 'CSV Data';
    case 'xlsx':
      return 'Excel Spreadsheet';
    case 'text_input':
      return 'Text Input';
    default:
      return 'Document';
  }
}

