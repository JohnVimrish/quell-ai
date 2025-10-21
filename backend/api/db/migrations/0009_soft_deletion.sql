-- =============================================
-- SOFT DELETION MIGRATION
-- =============================================
-- Add soft delete capability with audit trail

CREATE SCHEMA IF NOT EXISTS data_feeds;
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'ai_intelligence' AND table_name = 'document_deletion_log'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'data_feeds' AND table_name = 'document_deletion_log'
    ) THEN
        EXECUTE 'ALTER TABLE ai_intelligence.document_deletion_log SET SCHEMA data_feeds';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'document_deletion_log'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'data_feeds' AND table_name = 'document_deletion_log'
    ) THEN
        EXECUTE 'ALTER TABLE public.document_deletion_log SET SCHEMA data_feeds';
    END IF;
END$$;

-- Add soft delete columns to documents table (data_feeds schema)
ALTER TABLE data_feeds.documents ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT false;
ALTER TABLE data_feeds.documents ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE data_feeds.documents ADD COLUMN IF NOT EXISTS deleted_by INTEGER REFERENCES user_management.users(id);

-- Index for filtering non-deleted records (partial index for performance)
CREATE INDEX IF NOT EXISTS idx_documents_not_deleted ON data_feeds.documents(user_id, is_deleted) WHERE is_deleted = false;

-- Index for finding deleted documents
CREATE INDEX IF NOT EXISTS idx_documents_deleted ON data_feeds.documents(user_id, deleted_at) WHERE is_deleted = true;

-- Create deletion audit log table
CREATE TABLE IF NOT EXISTS data_feeds.document_deletion_log (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES data_feeds.documents(id),
    document_name TEXT NOT NULL,
    deleted_by INTEGER REFERENCES user_management.users(id),
    deleted_at TIMESTAMPTZ DEFAULT now(),
    reason TEXT,
    vector_metadata_snapshot JSONB,
    file_type VARCHAR(50),
    file_size_bytes BIGINT
);

-- Index for audit queries
CREATE INDEX IF NOT EXISTS idx_deletion_log_user ON data_feeds.document_deletion_log(deleted_by, deleted_at DESC);
CREATE INDEX IF NOT EXISTS idx_deletion_log_document ON data_feeds.document_deletion_log(document_id);

-- Add comments for documentation
COMMENT ON COLUMN data_feeds.documents.is_deleted IS 'Soft delete flag - if true, document is hidden from normal queries';
COMMENT ON COLUMN data_feeds.documents.deleted_at IS 'Timestamp when document was soft deleted';
COMMENT ON COLUMN data_feeds.documents.deleted_by IS 'User who deleted the document';
COMMENT ON TABLE data_feeds.document_deletion_log IS 'Audit log of document deletions with metadata snapshots';

