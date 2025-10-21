# Phase 2 Deployment Guide

## 🚀 Quick Deployment Steps

Follow these steps to deploy Phase 2 enhancements to your environment.

---

## Prerequisites

✅ Phase 1 data feeds system is deployed and working  
✅ PostgreSQL with pgvector extension enabled  
✅ Python environment with all dependencies installed  
✅ OLLama model accessible at configured path  
✅ Database backup completed  

---

## Step 1: Database Migrations

Run the migrations in order:

```bash
# Navigate to project root
cd /path/to/ai-call-copilot

# Activate Python virtual environment
source pvenv/bin/activate  # Linux/Mac
# OR
.\pvenv\Scripts\activate  # Windows

# Run migrations
psql -d your_database -f backend/api/db/migrations/0008_version_control.sql
psql -d your_database -f backend/api/db/migrations/0009_soft_deletion.sql
```

**Verify migrations:**
```sql
-- Check new columns exist
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'documents' 
AND column_name IN ('version', 'is_deleted', 'previous_embedding');

-- Check new tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_name IN ('document_versions', 'document_deletion_log');
```

---

## Step 2: Backend Code Deployment

```bash
# Pull latest code
git pull origin development

# Install any new dependencies (if added)
pip install -r requirements.txt

# Verify OLLama service configuration
python -c "
from backend.api.models.ollama_service import OllamaService
service = OllamaService('C:/Users/033690343/OneDrive - csulb/Models-LLM/Llama-3.2-1B-Instruct', 384)
print('OLLama available:', service.is_available())
print('Model info:', service.get_model_info())
"
```

---

## Step 3: Frontend Build

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (if not done)
npm install

# Build for production
npm run build

# Verify build artifacts
ls -la dist/
```

---

## Step 4: Configuration

### Update Environment Variables

Edit your `.env` or environment configuration:

```bash
# OLLama Configuration
OLLAMA_MODEL_PATH=C:/Users/033690343/OneDrive - csulb/Models-LLM/Llama-3.2-1B-Instruct
OLLAMA_EMBEDDING_DIM=384

# File Upload
DATA_FEEDS_UPLOAD_DIR=backend/uploads/data_feeds
MAX_FILE_SIZE_BYTES=104857600

# Version Control
VERSION_SIMILARITY_THRESHOLD=0.95

# Soft Deletion
SOFT_DELETE_RETENTION_DAYS=90
```

### Verify Configuration

```bash
# Check environment variables
echo $OLLAMA_MODEL_PATH
echo $OLLAMA_EMBEDDING_DIM

# OR on Windows
echo %OLLAMA_MODEL_PATH%
echo %OLLAMA_EMBEDDING_DIM%
```

---

## Step 5: Application Restart

### Development Environment

```bash
# Stop the backend server (Ctrl+C)

# Restart Flask backend
cd backend
python -m api.run
# OR
flask run

# Frontend should auto-reload if using Vite dev server
cd frontend
npm run dev
```

### Production Environment

```bash
# Restart gunicorn/uwsgi
sudo systemctl restart ai-call-copilot-backend

# Restart nginx (if serving frontend)
sudo systemctl restart nginx

# OR using PM2
pm2 restart ai-call-copilot
```

---

## Step 6: Verification Tests

### Test 1: Version Detection
```bash
# Upload a test file
curl -X POST http://localhost:5000/api/documents/upload \
  -H "Cookie: session=YOUR_SESSION" \
  -F "file=@test.txt" \
  -F "description=Test document"

# Expected: File uploaded successfully, version=1

# Upload the same file again
curl -X POST http://localhost:5000/api/documents/upload \
  -H "Cookie: session=YOUR_SESSION" \
  -F "file=@test.txt" \
  -F "description=Test document"

# Expected: File content unchanged, reprocessed=false
```

### Test 2: Soft Deletion
```bash
# Soft delete a document
curl -X DELETE http://localhost:5000/api/documents/1?reason=Test+deletion \
  -H "Cookie: session=YOUR_SESSION"

# Expected: {"message": "document deleted", "note": "..."}

# List deleted documents
curl http://localhost:5000/api/documents/deleted \
  -H "Cookie: session=YOUR_SESSION"

# Expected: {"documents": [{"id": 1, ...}]}
```

### Test 3: Restore Document
```bash
# Restore deleted document
curl -X POST http://localhost:5000/api/documents/1/restore \
  -H "Cookie: session=YOUR_SESSION"

# Expected: Document restored, appears in active list again
```

### Test 4: Version History
```bash
# Get version history
curl http://localhost:5000/api/documents/1/versions \
  -H "Cookie: session=YOUR_SESSION"

# Expected: {"versions": [...]}
```

---

## Step 7: Frontend Verification

Visit the Documents page and verify:

- [ ] **Upload Section**: File upload and text input work
- [ ] **Tab Navigation**: "Active Documents" and "Deleted Documents" tabs present
- [ ] **Active Tab**: Documents show version numbers
- [ ] **Version History**: "History" button appears for documents with version > 1
- [ ] **Delete Button**: Opens confirmation modal with reason field
- [ ] **Deleted Tab**: Shows soft-deleted documents
- [ ] **Restore Button**: Successfully restores deleted documents
- [ ] **Upload Feedback**: Shows "unchanged" or "updated to version X" messages

---

## Step 8: Monitor Logs

Watch application logs for any errors:

```bash
# Backend logs
tail -f backend/logs/app.log

# System logs (if using systemd)
journalctl -u ai-call-copilot-backend -f

# Check for specific errors
grep -i "error\|exception\|failed" backend/logs/app.log | tail -20
```

**Common issues to watch for:**
- OLLama model loading errors
- pgvector extension not found
- Migration not applied
- Permission issues with upload directory

---

## Step 9: Performance Tuning

### Index Performance Check
```sql
-- Check if indexes are being used
EXPLAIN ANALYZE 
SELECT * FROM documents 
WHERE user_id = 1 AND is_deleted = false;

-- Should show "Index Scan" not "Seq Scan"
```

### Query Performance
```sql
-- Check slow queries
SELECT query, calls, mean_exec_time 
FROM pg_stat_statements 
WHERE query LIKE '%documents%' 
ORDER BY mean_exec_time DESC 
LIMIT 10;
```

---

## Step 10: Setup Maintenance Jobs

### Cronjob for Old Document Cleanup

Create a cleanup script:

```python
# backend/maintenance/cleanup_old_deletions.py
from api.repositories.documents_repo import DocumentsRepository
from api.utils.config import AppConfig

config = AppConfig()
repo = DocumentsRepository(config.database_url, config.queries)

# Permanently delete documents soft-deleted > 90 days ago
count = repo.permanently_delete_old(days=90)
print(f"Permanently deleted {count} old documents")
```

Add to crontab:

```bash
# Run cleanup every Sunday at 2 AM
0 2 * * 0 cd /path/to/ai-call-copilot && source pvenv/bin/activate && python backend/maintenance/cleanup_old_deletions.py >> logs/cleanup.log 2>&1
```

---

## Rollback Plan

If issues are encountered:

### 1. Rollback Database
```sql
-- Drop new tables
DROP TABLE IF EXISTS document_deletion_log;
DROP TABLE IF EXISTS document_versions;

-- Remove new columns (only if necessary)
ALTER TABLE documents DROP COLUMN IF EXISTS version;
ALTER TABLE documents DROP COLUMN IF EXISTS is_deleted;
ALTER TABLE documents DROP COLUMN IF EXISTS deleted_at;
ALTER TABLE documents DROP COLUMN IF EXISTS deleted_by;
ALTER TABLE documents DROP COLUMN IF EXISTS previous_embedding;
ALTER TABLE documents DROP COLUMN IF EXISTS embedding_changed;
ALTER TABLE documents DROP COLUMN IF EXISTS last_modified_at;
```

### 2. Revert Code
```bash
# Checkout previous commit
git log --oneline  # Find last good commit
git checkout <commit-hash>

# Restart services
sudo systemctl restart ai-call-copilot-backend
```

### 3. Restore from Backup
```bash
# If database backup was made
pg_restore -d your_database backup_before_phase2.dump
```

---

## Post-Deployment Checklist

- [ ] All database migrations applied successfully
- [ ] New tables and columns exist
- [ ] Backend service restarted and running
- [ ] Frontend built and deployed
- [ ] Configuration variables set correctly
- [ ] Version detection working (test with duplicate upload)
- [ ] Soft deletion working (test delete and restore)
- [ ] Version history displaying correctly
- [ ] Deleted documents tab functioning
- [ ] No errors in application logs
- [ ] Database indexes created and being used
- [ ] Maintenance cronjob configured
- [ ] Monitoring/alerting configured for errors
- [ ] Documentation updated for team
- [ ] Stakeholders notified of new features

---

## Monitoring Recommendations

### Key Metrics to Monitor

1. **Upload Success Rate**: Track successful vs failed uploads
2. **Version Detection Rate**: % of uploads that create new versions
3. **Soft Deletion Usage**: Number of deletions and restores
4. **Query Performance**: Response times for document lists
5. **Embedding Comparison Time**: Time to compare embeddings
6. **Disk Usage**: Growth of document_versions table

### Alerts to Configure

- Database connection failures
- OLLama model unavailable
- Upload directory full
- Slow query threshold exceeded
- High error rate in logs

---

## Support and Troubleshooting

### Common Issues

**Issue**: Version always increments even for unchanged files  
**Solution**: Verify OLLama service is generating consistent embeddings. Check model is loaded correctly.

**Issue**: Deleted documents still visible  
**Solution**: Verify migration applied. Check `is_deleted` filter in repository queries.

**Issue**: Frontend not showing new features  
**Solution**: Clear browser cache. Rebuild frontend with `npm run build`. Check console for errors.

**Issue**: Version history empty  
**Solution**: Confirm document_versions table exists. Check snapshots are created during updates.

---

## Success Criteria

✅ All tests pass  
✅ No errors in logs  
✅ Version detection working correctly  
✅ Soft deletion and restore functional  
✅ Frontend displays new features  
✅ Performance within acceptable limits  
✅ Database migrations successful  
✅ Rollback plan tested and documented  

---

**Deployment Complete** 🎉

For issues or questions, refer to:
- `PHASE_2_IMPLEMENTATION_SUMMARY.md` for technical details
- `TROUBLESHOOTING.md` for common problems
- Team Slack channel for support

---

*Last Updated: October 21, 2025*

