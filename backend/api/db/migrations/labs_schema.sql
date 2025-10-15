CREATE TABLE IF NOT EXISTS ai_intelligence.labs_messages (
    message_id UUID PRIMARY KEY,
    convo_id UUID,
    user_id BIGINT REFERENCES user_management.users(id) ON DELETE SET NULL,
    source_lang TEXT,
    target_lang TEXT,
    raw_text TEXT NOT NULL,
    final_summary TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ai_intelligence.labs_message_chunks (
    chunk_id UUID PRIMARY KEY,
    message_id UUID REFERENCES ai_intelligence.labs_messages(message_id) ON DELETE CASCADE,
    ord INTEGER,
    text TEXT NOT NULL,
    embedding vector(1536)
);


CREATE TABLE IF NOT EXISTS ai_intelligence.labs_images (
    image_id UUID PRIMARY KEY,
    convo_id UUID,
    user_id BIGINT REFERENCES user_management.users(id) ON DELETE SET NULL,
    url TEXT,
    caption TEXT,
    embedding vector(1536),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_labs_messages_user
    ON ai_intelligence.labs_messages(user_id);




CREATE INDEX IF NOT EXISTS idx_labs_message_chunks_message
    ON ai_intelligence.labs_message_chunks(message_id);

CREATE INDEX IF NOT EXISTS idx_labs_message_chunks_embed
    ON ai_intelligence.labs_message_chunks USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 50);

CREATE INDEX IF NOT EXISTS idx_labs_images_embed
    ON ai_intelligence.labs_images USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 25);

