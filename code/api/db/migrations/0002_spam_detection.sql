CREATE TABLE IF NOT EXISTS document_embeddings (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
  document_type TEXT NOT NULL,
  document_id BIGINT,
  content TEXT NOT NULL,
  embedding vector(384),
  metadata JSONB,
  relevance_score FLOAT DEFAULT 0.0,
  usage_count INT DEFAULT 0,
  last_used TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS conversation_contexts (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
  conversation_id TEXT NOT NULL,
  conversation_type TEXT NOT NULL,
  context_data JSONB NOT NULL,
  embedding vector(384),
  entities_extracted JSONB,
  sentiment_score FLOAT DEFAULT 0.0,
  urgency_score FLOAT DEFAULT 0.0,
  confidence_score FLOAT DEFAULT 0.0,
  last_updated TIMESTAMPTZ DEFAULT now(),
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS spam_patterns (
  id BIGSERIAL PRIMARY KEY,
  pattern_type TEXT NOT NULL,
  pattern_data TEXT NOT NULL,
  embedding vector(384),
  confidence_score FLOAT NOT NULL,
  detection_count INT DEFAULT 0,
  false_positive_count INT DEFAULT 0,
  accuracy_rate FLOAT DEFAULT 0.0,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ml_model_metrics (
  id BIGSERIAL PRIMARY KEY,
  model_name TEXT NOT NULL,
  model_version TEXT NOT NULL,
  metric_type TEXT NOT NULL,
  metric_value FLOAT NOT NULL,
  dataset_size INT NOT NULL,
  training_time_seconds FLOAT,
  model_parameters JSONB,
  accuracy FLOAT DEFAULT 0.0,
  precision FLOAT DEFAULT 0.0,
  recall FLOAT DEFAULT 0.0,
  f1_score FLOAT DEFAULT 0.0,
  training_samples INT DEFAULT 0,
  last_trained TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_document_embeddings_user_type ON document_embeddings(user_id, document_type);
CREATE INDEX IF NOT EXISTS idx_conversation_contexts_user_conv ON conversation_contexts(user_id, conversation_id);
CREATE INDEX IF NOT EXISTS idx_spam_patterns_type_active ON spam_patterns(pattern_type, is_active);
CREATE INDEX IF NOT EXISTS idx_ml_metrics_model_version ON ml_model_metrics(model_name, model_version);