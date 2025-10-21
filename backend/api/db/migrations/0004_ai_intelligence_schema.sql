

-- =============================================
-- AI INTELLIGENCE SCHEMA
-- =============================================

CREATE TABLE IF NOT EXISTS ai_intelligence.feed_items (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES user_management.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    tags TEXT[] DEFAULT '{}',
    priority INTEGER DEFAULT 0 CHECK (priority BETWEEN 0 AND 10),
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'archived', 'expired')),
    is_sensitive BOOLEAN DEFAULT false,
    embedding vector(384),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    expires_at TIMESTAMPTZ DEFAULT (now() + INTERVAL '7 days'),
    last_accessed_at TIMESTAMPTZ,
    CONSTRAINT feed_items_title_not_empty CHECK (char_length(trim(title)) > 0),
    CONSTRAINT feed_items_body_not_empty CHECK (char_length(trim(body)) > 0),
    CONSTRAINT feed_items_expires_future CHECK (expires_at > created_at)
);

CREATE TABLE IF NOT EXISTS ai_intelligence.policies (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES user_management.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    body_text TEXT NOT NULL,
    policy_type TEXT DEFAULT 'general' CHECK (policy_type IN ('general', 'spam', 'emergency', 'business', 'personal')),
    tags TEXT[] DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 0 CHECK (priority BETWEEN 0 AND 10),
    embedding vector(384),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT policies_title_not_empty CHECK (char_length(trim(title)) > 0),
    CONSTRAINT policies_body_not_empty CHECK (char_length(trim(body_text)) > 0)
);

CREATE TABLE IF NOT EXISTS ai_intelligence.embeddings (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES user_management.users(id) ON DELETE CASCADE,
    content_type TEXT NOT NULL CHECK (content_type IN ('feed_item', 'policy', 'call_transcript', 'message', 'document')),
    content_id BIGINT NOT NULL,
    content_text TEXT NOT NULL,
    embedding vector(384) NOT NULL,
    model_name TEXT NOT NULL DEFAULT 'text-embedding-3-small',
    model_version TEXT DEFAULT '1.0',
    created_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT embeddings_content_not_empty CHECK (char_length(trim(content_text)) > 0),
    CONSTRAINT embeddings_user_content_unique UNIQUE(user_id, content_type, content_id)
);

CREATE TABLE IF NOT EXISTS ai_intelligence.spam_patterns (
    id BIGSERIAL PRIMARY KEY,
    pattern_type TEXT NOT NULL CHECK (pattern_type IN ('keyword', 'phone_pattern', 'content_pattern', 'behavioral')),
    pattern_value TEXT NOT NULL,
    confidence_score DECIMAL(3,2) NOT NULL CHECK (confidence_score BETWEEN 0 AND 1),
    is_active BOOLEAN DEFAULT true,
    source TEXT DEFAULT 'system' CHECK (source IN ('system', 'user', 'community', 'ml_model')),
    created_by BIGINT REFERENCES user_management.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT spam_patterns_value_not_empty CHECK (char_length(trim(pattern_value)) > 0)
);

CREATE TABLE IF NOT EXISTS ai_intelligence.ml_model_metrics (
    id BIGSERIAL PRIMARY KEY,
    model_name TEXT NOT NULL,
    model_version TEXT NOT NULL,
    metric_type TEXT NOT NULL CHECK (metric_type IN ('accuracy', 'precision', 'recall', 'f1_score', 'auc_roc')),
    metric_value DECIMAL(5,4) NOT NULL CHECK (metric_value BETWEEN 0 AND 1),
    dataset_size INTEGER NOT NULL CHECK (dataset_size > 0),
    evaluation_date TIMESTAMPTZ DEFAULT now(),
    metadata JSONB DEFAULT '{}',
    CONSTRAINT ml_metrics_model_version_metric_unique UNIQUE(model_name, model_version, metric_type)
);

CREATE TABLE IF NOT EXISTS ai_intelligence.voice_models (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES user_management.users(id) ON DELETE CASCADE,
    model_name TEXT NOT NULL,
    voice_sample_uri TEXT,
    model_uri TEXT,
    training_status TEXT DEFAULT 'pending' CHECK (training_status IN ('pending', 'training', 'completed', 'failed')),
    quality_score DECIMAL(3,2) CHECK (quality_score BETWEEN 0 AND 1),
    is_active BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT voice_models_user_name_unique UNIQUE(user_id, model_name)
);

-- Indexes for ai_intelligence schema
CREATE INDEX IF NOT EXISTS idx_feed_items_user_id ON ai_intelligence.feed_items(user_id);
CREATE INDEX IF NOT EXISTS idx_feed_items_status ON ai_intelligence.feed_items(status, expires_at);
CREATE INDEX IF NOT EXISTS idx_feed_items_active ON ai_intelligence.feed_items(user_id, status, expires_at) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_feed_items_priority ON ai_intelligence.feed_items(priority DESC, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_feed_items_tags ON ai_intelligence.feed_items USING gin(tags);
CREATE INDEX IF NOT EXISTS idx_feed_items_embedding ON ai_intelligence.feed_items USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_policies_user_id ON ai_intelligence.policies(user_id);
CREATE INDEX IF NOT EXISTS idx_policies_active ON ai_intelligence.policies(user_id, is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_policies_type ON ai_intelligence.policies(policy_type);
CREATE INDEX IF NOT EXISTS idx_policies_priority ON ai_intelligence.policies(priority DESC, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_policies_embedding ON ai_intelligence.policies USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_embeddings_user_content ON ai_intelligence.embeddings(user_id, content_type, content_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_type ON ai_intelligence.embeddings(content_type);
CREATE INDEX IF NOT EXISTS idx_embeddings_vector ON ai_intelligence.embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_spam_patterns_type ON ai_intelligence.spam_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_spam_patterns_active ON ai_intelligence.spam_patterns(is_active, confidence_score) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_spam_patterns_value ON ai_intelligence.spam_patterns(pattern_value);

CREATE INDEX IF NOT EXISTS idx_ml_model_metrics_model ON ai_intelligence.ml_model_metrics(model_name, model_version);
CREATE INDEX IF NOT EXISTS idx_ml_model_metrics_date ON ai_intelligence.ml_model_metrics(evaluation_date);

CREATE INDEX IF NOT EXISTS idx_voice_models_user ON ai_intelligence.voice_models(user_id);
CREATE INDEX IF NOT EXISTS idx_voice_models_active ON ai_intelligence.voice_models(user_id, is_active) WHERE is_active = true;
