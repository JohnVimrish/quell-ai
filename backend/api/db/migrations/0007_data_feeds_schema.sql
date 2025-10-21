-- =============================================
-- DATA FEEDS SCHEMA ENHANCEMENTS
-- =============================================
-- Add columns to documents table for data feed capabilities

CREATE SCHEMA IF NOT EXISTS data_feeds;
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'ai_intelligence' AND table_name = 'documents'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'data_feeds' AND table_name = 'documents'
    ) THEN
        EXECUTE 'ALTER TABLE ai_intelligence.documents SET SCHEMA data_feeds';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'documents'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'data_feeds' AND table_name = 'documents'
    ) THEN
        EXECUTE 'ALTER TABLE public.documents SET SCHEMA data_feeds';
    END IF;
END$$;

-- Target schema: data_feeds
ALTER TABLE data_feeds.documents ADD COLUMN IF NOT EXISTS file_size_bytes BIGINT;
ALTER TABLE data_feeds.documents ADD COLUMN IF NOT EXISTS file_type VARCHAR(50);
ALTER TABLE data_feeds.documents ADD COLUMN IF NOT EXISTS original_content TEXT;
ALTER TABLE data_feeds.documents ADD COLUMN IF NOT EXISTS processed_content TEXT;
ALTER TABLE data_feeds.documents ADD COLUMN IF NOT EXISTS content_metadata JSONB DEFAULT '{}';
ALTER TABLE data_feeds.documents ADD COLUMN IF NOT EXISTS embedding vector(384);
ALTER TABLE data_feeds.documents ADD COLUMN IF NOT EXISTS vector_metadata JSONB DEFAULT '{}';
ALTER TABLE data_feeds.documents ADD COLUMN IF NOT EXISTS ollama_model VARCHAR(100);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_documents_file_type ON data_feeds.documents(file_type);
CREATE INDEX IF NOT EXISTS idx_documents_embedding ON data_feeds.documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_documents_user_file_type ON data_feeds.documents(user_id, file_type);

-- Add comments for documentation
COMMENT ON COLUMN data_feeds.documents.file_size_bytes IS 'Size of uploaded file in bytes';
COMMENT ON COLUMN data_feeds.documents.file_type IS 'Type of file: txt, csv, xlsx, or text_input';
COMMENT ON COLUMN data_feeds.documents.original_content IS 'Raw content from uploaded file';
COMMENT ON COLUMN data_feeds.documents.processed_content IS 'Cleaned and parsed content ready for AI processing';
COMMENT ON COLUMN data_feeds.documents.content_metadata IS 'Extraction metadata: row counts, columns, parsing info';
COMMENT ON COLUMN data_feeds.documents.embedding IS 'OLLama-generated 384-dimensional embedding vector';
COMMENT ON COLUMN data_feeds.documents.vector_metadata IS 'Mapping of key concepts to table locations for semantic retrieval';
COMMENT ON COLUMN data_feeds.documents.ollama_model IS 'Name/version of OLLama model used for processing';

