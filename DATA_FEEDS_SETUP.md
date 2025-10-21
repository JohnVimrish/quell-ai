# Data Feeds with OLLama Integration - Setup Guide

## Overview

This implementation adds a comprehensive data feeds system to the AI Call Copilot platform, allowing users to upload text-based files (txt, csv, xlsx) or submit text directly for AI-powered semantic search and retrieval using a local OLLama model.

## Features Implemented

### Backend
1. **OLLama Integration Service** (`backend/api/models/ollama_service.py`)
   - Local LLM integration for embeddings and response generation
   - 384-dimensional vector embeddings
   - Batch processing support
   - Graceful fallback when model unavailable

2. **File Processing Utilities** (`backend/api/utils/file_processors.py`)
   - Support for .txt, .csv, and .xlsx files
   - 100MB file size limit with validation
   - Content extraction and parsing
   - Metadata generation

3. **Metadata Extraction** (`backend/api/utils/metadata_extractor.py`)
   - Key concept extraction (emails, names, documents, key phrases)
   - Vector metadata mapping for semantic retrieval
   - Entity recognition

4. **Database Schema** (`backend/api/db/migrations/0007_data_feeds_schema.sql`)
   - New columns in documents table for data feeds
   - Vector storage with pgvector
   - Content and metadata storage
   - Indexes for efficient querying

5. **Enhanced Document Model** (`backend/functionalities/document.py`)
   - Added data feed specific fields
   - Vector embedding support
   - Content storage

6. **Enhanced Repository** (`backend/api/repositories/documents_repo.py`)
   - Vector similarity search
   - Data feed creation
   - Content retrieval methods

7. **New API Endpoints** (`backend/api/controllers/documents_controller.py`)
   - `POST /api/documents/upload` - File upload
   - `POST /api/documents/text` - Text submission
   - `GET /api/documents/<id>/content` - Content retrieval

### Frontend
1. **Upload Utilities** (`frontend/src/utils/documentUpload.ts`)
   - File validation
   - Upload with progress tracking
   - Text submission
   - Helper functions for formatting

2. **Enhanced Documents Page** (`frontend/src/pages/DocumentsPage.tsx`)
   - Drag-and-drop file upload
   - Text input interface
   - Progress indicators
   - Enhanced document listing with data feed info

## Installation & Setup

### Prerequisites

1. **Python Dependencies**
   ```bash
   pip install transformers torch openpyxl pgvector
   ```

2. **Database Migration**
   Run the migration to add new columns:
   ```bash
   psql -U your_user -d your_database -f backend/api/db/migrations/0007_data_feeds_schema.sql
   ```

3. **Environment Variables**
   Add to your `.env` file:
   ```env
   # OLLama Model Configuration
   OLLAMA_MODEL_PATH=C:/Users/033690343/OneDrive - csulb/Models-LLM/Llama-3.2-1B-Instruct
   OLLAMA_EMBEDDING_DIM=384
   
   # Data Feeds Upload Directory
   DATA_FEEDS_UPLOAD_DIR=backend/uploads/data_feeds
   ```

### OLLama Model Setup

1. Ensure the OLLama model is downloaded and available at the configured path
2. The model should be compatible with HuggingFace `transformers` library
3. Model should support embedding generation

### Directory Structure

Ensure the upload directory exists:
```bash
mkdir -p backend/uploads/data_feeds
```

## Usage

### Uploading a File

1. Navigate to the Documents page
2. Click "📁 Upload File"
3. Drag and drop a file or click to browse
4. Optionally add a description
5. Click "Upload"

**Supported File Types:**
- `.txt` - Plain text files
- `.csv` - Comma-separated values
- `.xlsx` - Excel spreadsheets

**File Size Limit:** 100 MB

### Submitting Text

1. Navigate to the Documents page
2. Click "📝 Enter Text"
3. Enter a name for the input
4. Paste or type your content
5. Optionally add a description
6. Click "Submit"

### What Happens During Processing

1. **File Upload/Text Submission**
   - File is validated for size and type
   - Content is extracted and parsed

2. **Content Processing**
   - Key concepts are extracted (emails, names, documents, phrases)
   - Text is cleaned and structured

3. **OLLama Processing**
   - Embedding vector is generated (384-dim)
   - Content is vectorized for semantic search

4. **Metadata Generation**
   - Vector metadata mapping is created
   - Concepts are linked to document locations

5. **Database Storage**
   - Original content is stored
   - Processed content is saved
   - Embedding vector is indexed
   - Metadata is structured as JSON

## API Reference

### Upload File
```http
POST /api/documents/upload
Content-Type: multipart/form-data

Parameters:
- file: File (required) - .txt, .csv, or .xlsx file
- description: string (optional) - File description
- classification: string (optional) - Document classification

Response: 201 Created
{
  "id": 123,
  "name": "data.csv",
  "file_type": "csv",
  "file_size_bytes": 1024000,
  "has_embedding": true,
  "content_metadata": {...},
  "vector_metadata": {...},
  ...
}
```

### Submit Text
```http
POST /api/documents/text
Content-Type: application/json

Body:
{
  "name": "Meeting Notes",
  "content": "Text content here...",
  "description": "Optional description",
  "classification": "internal"
}

Response: 201 Created
{
  "id": 124,
  "name": "Meeting Notes",
  "file_type": "text_input",
  "has_embedding": true,
  ...
}
```

### Get Document Content
```http
GET /api/documents/<id>/content

Response: 200 OK
{
  "id": 123,
  "name": "data.csv",
  "file_type": "csv",
  "processed_content": "Cleaned content...",
  "original_content": "Raw content...",
  "content_metadata": {...},
  "vector_metadata": {...}
}
```

## Vector Metadata Format

The vector metadata follows this structure:
```json
{
  "vector_email_abc123def": ["doc_123_email"],
  "vector_document_xyz789": ["doc_123_document"],
  "vector_phrase_qrs456": ["doc_123_phrase"],
  "_meta": {
    "total_keys": 3,
    "document_id": 123,
    "entity_count": 5
  }
}
```

This allows the OLLama model to quickly locate which parts of the database contain relevant information for a given query.

## Semantic Search Integration

The system can be queried for similar documents:

```python
from api.repositories.documents_repo import DocumentsRepository

repo = DocumentsRepository(database_url, queries)

# Generate query embedding using OLLama
query_embedding = ollama_service.generate_embedding("classified document")

# Search for similar documents
results = repo.search_by_vector(
    query_embedding=query_embedding,
    user_id=1,
    limit=5,
    file_types=["txt", "csv"]
)

# Results include similarity scores
for doc in results:
    print(f"{doc['name']}: {doc['similarity_score']}")
```

## Troubleshooting

### OLLama Model Not Loading

**Issue:** Model fails to initialize
**Solutions:**
- Verify model path is correct
- Check that transformers and torch are installed
- Ensure sufficient disk space and memory
- Check logs for specific error messages

**Fallback:** The system will continue to function without embeddings, storing content for manual retrieval.

### File Upload Fails

**Issue:** Files larger than 100MB rejected
**Solution:** Use designated SharePoint for large files (message is shown to user)

**Issue:** Unsupported file type
**Solution:** Convert to .txt, .csv, or .xlsx format

### Vector Search Not Working

**Issue:** No results from semantic search
**Checks:**
- Verify pgvector extension is installed
- Check that embeddings are being generated
- Ensure vector index exists on documents table
- Confirm OLLama service is available

## Performance Considerations

1. **Large Files**
   - Files up to 100MB supported
   - Processing time scales with file size
   - Consider background processing for very large files

2. **Batch Processing**
   - Use `batch_embed()` for multiple documents
   - More efficient than individual embedding calls

3. **Vector Search**
   - Indexed for fast similarity queries
   - Performance degrades with very large document collections
   - Consider partitioning for 10k+ documents

## Security Notes

1. **File Validation**
   - File size strictly enforced (100MB)
   - File type whitelist (txt, csv, xlsx)
   - Filename sanitization

2. **Access Control**
   - All endpoints require authentication
   - Documents scoped to user_id
   - Existing document permissions apply

3. **Content Storage**
   - Original content stored in database
   - Files also saved to secure upload directory
   - Cleanup policies should be configured

## Future Enhancements

Potential improvements:
- Background job processing for large files
- Batch upload interface
- Document versioning
- Advanced vector search filters
- Integration with existing RAG system
- Export functionality
- Document preview
- Content editing

## Support

For issues or questions:
1. Check application logs in `logs/` directory
2. Verify environment variables are set correctly
3. Test OLLama service independently
4. Check database migration status
5. Review API error responses for details

