# Data Feeds Deployment Checklist

## Pre-Deployment Verification

### ✅ Files Created/Modified
- [x] `backend/api/models/ollama_service.py` - OLLama integration
- [x] `backend/api/utils/file_processors.py` - File processing
- [x] `backend/api/utils/metadata_extractor.py` - Metadata extraction
- [x] `backend/api/db/migrations/0007_data_feeds_schema.sql` - Database migration
- [x] `backend/functionalities/document.py` - Enhanced document model
- [x] `backend/api/repositories/documents_repo.py` - Repository methods
- [x] `backend/api/controllers/documents_controller.py` - API endpoints
- [x] `backend/api/app.py` - OLLama service initialization
- [x] `frontend/src/utils/documentUpload.ts` - Upload utilities
- [x] `frontend/src/pages/DocumentsPage.tsx` - Enhanced UI
- [x] `backend/tests/test_data_feeds.py` - Test suite
- [x] `DATA_FEEDS_SETUP.md` - Setup documentation
- [x] `IMPLEMENTATION_SUMMARY.md` - Implementation summary

## Deployment Steps

### 1. Backend Setup

#### Install Python Dependencies
```bash
# Activate virtual environment
source pvenv/bin/activate  # Linux/Mac
# or
pvenv\Scripts\activate  # Windows

# Install required packages
pip install transformers torch openpyxl pgvector

# Verify installation
python -c "import transformers; import torch; import openpyxl; print('All packages installed')"
```

**Status:** [ ] Complete

#### Configure Environment Variables
Add to your `.env` file or environment:
```env
# OLLama Model Configuration
OLLAMA_MODEL_PATH=C:/Users/033690343/OneDrive - csulb/Models-LLM/Llama-3.2-1B-Instruct
OLLAMA_EMBEDDING_DIM=384

# Upload Directory
DATA_FEEDS_UPLOAD_DIR=backend/uploads/data_feeds
```

**Status:** [ ] Complete

#### Create Upload Directory
```bash
mkdir -p backend/uploads/data_feeds
chmod 755 backend/uploads/data_feeds
```

**Status:** [ ] Complete

### 2. Database Migration

#### Run Migration Script
```bash
# Replace with your actual database credentials
psql -U your_username -d your_database_name -f backend/api/db/migrations/0007_data_feeds_schema.sql

# Or if using environment variable
psql $DATABASE_URL -f backend/api/db/migrations/0007_data_feeds_schema.sql
```

**Status:** [ ] Complete

#### Verify Migration
```sql
-- Connect to database and verify columns exist
\d documents

-- Should show new columns:
-- file_size_bytes, file_type, original_content, processed_content,
-- content_metadata, embedding, vector_metadata, ollama_model
```

**Status:** [ ] Complete

### 3. OLLama Model Setup

#### Verify Model Path
```bash
# Check if model exists at specified path
ls -la "C:/Users/033690343/OneDrive - csulb/Models-LLM/Llama-3.2-1B-Instruct"

# Should contain model files (config.json, pytorch_model.bin, etc.)
```

**Status:** [ ] Complete

#### Test Model Loading (Optional)
```python
from api.models.ollama_service import OllamaService

service = OllamaService()
print(f"Model loaded: {service.is_available()}")
print(f"Model info: {service.get_model_info()}")

# Test embedding
embedding = service.generate_embedding("test text")
print(f"Embedding dimension: {len(embedding) if embedding else 'None'}")
```

**Status:** [ ] Complete

### 4. Application Restart

#### Backend
```bash
# Stop current backend process
# Then restart
cd backend/api
python run.py

# Or if using gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:create_app()
```

**Status:** [ ] Complete

#### Frontend
```bash
cd frontend
npm run build  # For production
# or
npm run dev    # For development
```

**Status:** [ ] Complete

### 5. Testing

#### Run Unit Tests
```bash
cd backend
pytest tests/test_data_feeds.py -v

# Expected: All tests should pass or gracefully handle missing model
```

**Status:** [ ] Complete

#### Manual Testing - File Upload

1. Navigate to http://localhost:5173/documents (or your URL)
2. Click "📁 Upload File"
3. Select or drag a small .txt file
4. Add optional description
5. Click "Upload"
6. Verify success message appears
7. Check document appears in list with correct metadata

**Status:** [ ] Complete

#### Manual Testing - Text Input

1. Navigate to Documents page
2. Click "📝 Enter Text"
3. Enter name: "Test Input"
4. Enter content: "if john.vimri@gmail.com asks for document X, refer to location Y"
5. Click "Submit"
6. Verify success message
7. Check document appears in list

**Status:** [ ] Complete

#### Test API Endpoints

```bash
# Test upload endpoint (requires authentication)
curl -X POST http://localhost:5000/api/documents/upload \
  -H "Cookie: session=your_session_cookie" \
  -F "file=@test.txt" \
  -F "description=Test file"

# Test text submission
curl -X POST http://localhost:5000/api/documents/text \
  -H "Content-Type: application/json" \
  -H "Cookie: session=your_session_cookie" \
  -d '{"name":"Test","content":"Test content"}'

# Test list documents (should show new fields)
curl http://localhost:5000/api/documents \
  -H "Cookie: session=your_session_cookie"
```

**Status:** [ ] Complete

### 6. Validation Checks

#### Database Validation
```sql
-- Check that documents are being stored with new fields
SELECT id, name, file_type, file_size_bytes, 
       has_embedding, ollama_model
FROM documents
WHERE file_type IS NOT NULL
LIMIT 5;

-- Verify vector metadata is populated
SELECT id, name, vector_metadata
FROM documents
WHERE vector_metadata IS NOT NULL;
```

**Status:** [ ] Complete

#### File Storage Validation
```bash
# Check that files are being saved
ls -la backend/uploads/data_feeds/

# Should show uploaded files with naming pattern:
# {user_id}_{timestamp}_{filename}
```

**Status:** [ ] Complete

#### OLLama Integration Check
```bash
# Check application logs for OLLama initialization
tail -f logs/application.log | grep -i ollama

# Should see messages like:
# "Loading OLLama model from ..."
# "Model loaded successfully"
```

**Status:** [ ] Complete

### 7. Performance Testing

#### Test Large File
1. Create or download a ~50MB text file
2. Upload via UI
3. Monitor upload progress
4. Verify successful processing
5. Check response time (should be reasonable)

**Status:** [ ] Complete

#### Test File Size Limit
1. Attempt to upload file > 100MB
2. Should receive error: "File size exceeds 100 MB limit"
3. Message should mention SharePoint

**Status:** [ ] Complete

#### Test Unsupported File Type
1. Attempt to upload .pdf or .docx
2. Should receive error about unsupported file type
3. Should list supported types

**Status:** [ ] Complete

### 8. Security Verification

#### Authentication Check
```bash
# Attempt to upload without authentication
curl -X POST http://localhost:5000/api/documents/upload \
  -F "file=@test.txt"

# Should return 401 Unauthorized
```

**Status:** [ ] Complete

#### Access Control Check
1. Login as User A
2. Upload a document
3. Note the document ID
4. Logout and login as User B
5. Attempt to access User A's document
6. Should not be visible or accessible

**Status:** [ ] Complete

## Post-Deployment

### Monitor Logs
```bash
# Watch for errors
tail -f logs/application.log

# Check for common issues:
# - Model loading failures
# - File processing errors
# - Database connection issues
# - Memory problems
```

**Status:** [ ] Complete

### Performance Monitoring
- [ ] Monitor memory usage (OLLama model can use 2-4GB)
- [ ] Check disk space in upload directory
- [ ] Monitor database size growth
- [ ] Track API response times

### User Training
- [ ] Share `DATA_FEEDS_SETUP.md` with users
- [ ] Demonstrate file upload process
- [ ] Explain file size limits
- [ ] Show how to use text input

## Rollback Plan

If issues occur, rollback steps:

1. **Stop Application**
   ```bash
   # Stop backend and frontend processes
   ```

2. **Revert Database Migration**
   ```sql
   -- Remove added columns if needed
   ALTER TABLE documents DROP COLUMN IF EXISTS file_size_bytes;
   ALTER TABLE documents DROP COLUMN IF EXISTS file_type;
   -- etc.
   ```

3. **Revert Code Changes**
   ```bash
   git checkout previous_commit_hash
   ```

4. **Restart Application**

## Success Criteria

- [x] All files created/modified as per plan
- [ ] Database migration successful
- [ ] OLLama service initializes (or gracefully fails)
- [ ] File upload works end-to-end
- [ ] Text submission works end-to-end
- [ ] Documents appear in list with metadata
- [ ] Authentication and access control working
- [ ] File size validation working
- [ ] No linter errors
- [ ] Unit tests pass
- [ ] Application stable under normal load

## Sign-Off

**Deployed By:** ___________________  
**Date:** ___________________  
**Environment:** [ ] Development [ ] Staging [ ] Production  
**Issues Encountered:** ___________________  
**Notes:** ___________________

---

## Quick Reference

### Key Endpoints
- POST /api/documents/upload - Upload file
- POST /api/documents/text - Submit text
- GET /api/documents - List documents
- GET /api/documents/<id>/content - Get content

### Supported File Types
- .txt (text files)
- .csv (comma-separated values)
- .xlsx (Excel spreadsheets)

### File Size Limit
- Maximum: 100 MB
- Validated on both client and server

### Environment Variables
```
OLLAMA_MODEL_PATH=C:/Users/033690343/OneDrive - csulb/Models-LLM/Llama-3.2-1B-Instruct
OLLAMA_EMBEDDING_DIM=384
DATA_FEEDS_UPLOAD_DIR=backend/uploads/data_feeds
```

---

**For detailed information, see:**
- `DATA_FEEDS_SETUP.md` - Setup guide
- `IMPLEMENTATION_SUMMARY.md` - Technical details
- `backend/tests/test_data_feeds.py` - Test cases

