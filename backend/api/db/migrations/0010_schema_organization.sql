-- =============================================
-- SCHEMA ORGANIZATION MIGRATION
-- =============================================
-- Organize data feeds into separate schemas by business function

-- Create schemas for logical organization
CREATE SCHEMA IF NOT EXISTS data_feeds;
CREATE SCHEMA IF NOT EXISTS data_feeds_vectors;
CREATE SCHEMA IF NOT EXISTS data_feeds_metadata;

-- Grant usage on schemas (adjust as needed for your user)
GRANT USAGE ON SCHEMA data_feeds TO PUBLIC;
GRANT USAGE ON SCHEMA data_feeds_vectors TO PUBLIC;
GRANT USAGE ON SCHEMA data_feeds_metadata TO PUBLIC;

-- Create vector embeddings table in dedicated schema
CREATE TABLE IF NOT EXISTS data_feeds_vectors.embeddings (
    id SERIAL PRIMARY KEY,
    file_id INTEGER NOT NULL, -- References documents(id) or data_feeds.input_files(id)
    chunk_index INTEGER DEFAULT 0,
    embedding vector(384) NOT NULL,
    content_snippet TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Create concepts table for extracted entities
CREATE TABLE IF NOT EXISTS data_feeds_metadata.concepts (
    id SERIAL PRIMARY KEY,
    file_id INTEGER NOT NULL,
    concept_type VARCHAR(50) NOT NULL, -- email, phone, name, phrase, document
    concept_value TEXT NOT NULL,
    confidence_score FLOAT DEFAULT 1.0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Create vector mappings table for key-to-location mapping
CREATE TABLE IF NOT EXISTS data_feeds_metadata.vector_mappings (
    id SERIAL PRIMARY KEY,
    vector_key VARCHAR(100) NOT NULL UNIQUE,
    table_references TEXT[] NOT NULL,
    file_id INTEGER,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_embeddings_file ON data_feeds_vectors.embeddings(file_id, is_active);
CREATE INDEX IF NOT EXISTS idx_embeddings_vector ON data_feeds_vectors.embeddings 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_embeddings_active ON data_feeds_vectors.embeddings(is_active) WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_concepts_file ON data_feeds_metadata.concepts(file_id, concept_type);
CREATE INDEX IF NOT EXISTS idx_concepts_type ON data_feeds_metadata.concepts(concept_type, is_active);
CREATE INDEX IF NOT EXISTS idx_concepts_value ON data_feeds_metadata.concepts(concept_value);

CREATE INDEX IF NOT EXISTS idx_vector_mappings_key ON data_feeds_metadata.vector_mappings(vector_key);
CREATE INDEX IF NOT EXISTS idx_vector_mappings_file ON data_feeds_metadata.vector_mappings(file_id);

-- Add comments for documentation
COMMENT ON SCHEMA data_feeds IS 'Schema for data feeds input files and related tables';
COMMENT ON SCHEMA data_feeds_vectors IS 'Schema for vector embeddings storage';
COMMENT ON SCHEMA data_feeds_metadata IS 'Schema for extracted metadata, concepts, and mappings';

COMMENT ON TABLE data_feeds_vectors.embeddings IS 'Vector embeddings for document chunks';
COMMENT ON TABLE data_feeds_metadata.concepts IS 'Extracted concepts from documents (emails, names, etc.)';
COMMENT ON TABLE data_feeds_metadata.vector_mappings IS 'Mapping of vector keys to database table locations';

-- Note: The documents table remains in the public/default schema for backward compatibility
-- New features can optionally use these schema-organized tables

