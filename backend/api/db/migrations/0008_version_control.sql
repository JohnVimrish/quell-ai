-- =============================================
-- VERSION CONTROL MIGRATION
-- =============================================
-- Add version tracking and history for documents

CREATE SCHEMA IF NOT EXISTS data_feeds;
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'ai_intelligence' AND table_name = 'document_versions'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'data_feeds' AND table_name = 'document_versions'
    ) THEN
        EXECUTE 'ALTER TABLE ai_intelligence.document_versions SET SCHEMA data_feeds';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'document_versions'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'data_feeds' AND table_name = 'document_versions'
    ) THEN
        EXECUTE 'ALTER TABLE public.document_versions SET SCHEMA data_feeds';
    END IF;
END$$;

-- Add version control columns to documents table (data_feeds schema)
ALTER TABLE data_feeds.documents ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1;
ALTER TABLE data_feeds.documents ADD COLUMN IF NOT EXISTS previous_embedding vector(384);
ALTER TABLE data_feeds.documents ADD COLUMN IF NOT EXISTS last_modified_at TIMESTAMPTZ;
ALTER TABLE data_feeds.documents ADD COLUMN IF NOT EXISTS embedding_changed BOOLEAN DEFAULT false;

-- Create version history table
CREATE TABLE IF NOT EXISTS data_feeds.document_versions (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES data_feeds.documents(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    embedding vector(384),
    content_snapshot TEXT,
    metadata_snapshot JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    created_by INTEGER REFERENCES user_management.users(id)
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_document_versions_document ON data_feeds.document_versions(document_id, version DESC);
CREATE INDEX IF NOT EXISTS idx_documents_version ON data_feeds.documents(user_id, version);

-- Add comments for documentation
COMMENT ON COLUMN data_feeds.documents.version IS 'Version number of the document, incremented on content changes';
COMMENT ON COLUMN data_feeds.documents.previous_embedding IS 'Previous embedding vector for comparison';
COMMENT ON COLUMN data_feeds.documents.last_modified_at IS 'Timestamp of last content modification';
COMMENT ON COLUMN data_feeds.documents.embedding_changed IS 'Flag indicating if embedding changed in last update';
COMMENT ON TABLE data_feeds.document_versions IS 'Historical versions of documents for audit and recovery';

