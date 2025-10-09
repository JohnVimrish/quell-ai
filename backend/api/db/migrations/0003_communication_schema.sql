
-- =============================================
-- COMMUNICATION SCHEMA (CALLS & MESSAGES)
-- =============================================

CREATE TABLE IF NOT EXISTS communication.calls (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES user_management.users(id) ON DELETE CASCADE,
    contact_id BIGINT REFERENCES user_management.contacts(id) ON DELETE SET NULL,
    from_number TEXT NOT NULL,
    to_number TEXT NOT NULL,
    direction TEXT NOT NULL CHECK (direction IN ('incoming', 'outgoing')),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'ringing', 'answered', 'completed', 'failed', 'busy', 'no_answer')),
    started_at TIMESTAMPTZ DEFAULT now(),
    answered_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    duration_seconds INTEGER DEFAULT 0 CHECK (duration_seconds >= 0),
    intent TEXT,
    urgency TEXT CHECK (urgency IN ('low', 'medium', 'high', 'urgent')),
    outcome TEXT,
    transcript TEXT,
    transcript_confidence DECIMAL(3,2) CHECK (transcript_confidence BETWEEN 0 AND 1),
    recording_uri TEXT,
    recording_duration_seconds INTEGER CHECK (recording_duration_seconds >= 0),
    spam_score INTEGER DEFAULT 0 CHECK (spam_score BETWEEN 0 AND 100),
    is_spam BOOLEAN DEFAULT false,
    ai_handled BOOLEAN DEFAULT false,
    policy_ids BIGINT[],
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT calls_phone_format_from CHECK (from_number ~ '^\+?[1-9]\d{1,14}'),
    CONSTRAINT calls_phone_format_to CHECK (to_number ~ '^\+?[1-9]\d{1,14}'),
    CONSTRAINT calls_duration_logical CHECK (ended_at IS NULL OR answered_at IS NULL OR ended_at >= answered_at),
    CONSTRAINT calls_answered_logical CHECK (answered_at IS NULL OR answered_at >= started_at)
);

CREATE TABLE IF NOT EXISTS communication.messages (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES user_management.users(id) ON DELETE CASCADE,
    contact_id BIGINT REFERENCES user_management.contacts(id) ON DELETE SET NULL,
    conversation_id UUID DEFAULT uuid_generate_v4(),
    phone_number TEXT NOT NULL,
    direction TEXT NOT NULL CHECK (direction IN ('incoming', 'outgoing')),
    message_body TEXT NOT NULL,
    message_type TEXT DEFAULT 'text' CHECK (message_type IN ('text', 'media', 'location', 'contact')),
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'delivered', 'read', 'failed')),
    is_spam BOOLEAN DEFAULT false,
    spam_score INTEGER DEFAULT 0 CHECK (spam_score BETWEEN 0 AND 100),
    is_read BOOLEAN DEFAULT false,
    intent TEXT,
    sentiment TEXT CHECK (sentiment IN ('positive', 'negative', 'neutral')),
    ai_response TEXT,
    media_urls TEXT[],
    metadata JSONB DEFAULT '{}',
    sent_at TIMESTAMPTZ,
    received_at TIMESTAMPTZ DEFAULT now(),
    read_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT messages_phone_format CHECK (phone_number ~ '^\+?[1-9]\d{1,14}'),
    CONSTRAINT messages_body_not_empty CHECK (char_length(trim(message_body)) > 0),
    CONSTRAINT messages_read_logic CHECK (is_read = false OR read_at IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS communication.conversation_contexts (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES user_management.users(id) ON DELETE CASCADE,
    conversation_id UUID NOT NULL,
    context_type TEXT NOT NULL CHECK (context_type IN ('call', 'message_thread', 'mixed')),
    summary TEXT,
    key_topics TEXT[],
    sentiment_analysis JSONB,
    participant_count INTEGER DEFAULT 2 CHECK (participant_count >= 2),
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT conversation_contexts_start_time_logic CHECK (end_time IS NULL OR start_time <= end_time),
    CONSTRAINT conversation_contexts_time_logic CHECK (end_time IS NULL OR end_time >= start_time),
    CONSTRAINT conversation_contexts_user_conv_unique UNIQUE(user_id, conversation_id)
);

-- Indexes for communication schema
CREATE INDEX IF NOT EXISTS idx_calls_user_id ON communication.calls(user_id);
CREATE INDEX IF NOT EXISTS idx_calls_contact_id ON communication.calls(contact_id);
CREATE INDEX IF NOT EXISTS idx_calls_from_number ON communication.calls(from_number);
CREATE INDEX IF NOT EXISTS idx_calls_started_at ON communication.calls(started_at);
CREATE INDEX IF NOT EXISTS idx_calls_direction ON communication.calls(direction);
CREATE INDEX IF NOT EXISTS idx_calls_status ON communication.calls(status);
CREATE INDEX IF NOT EXISTS idx_calls_spam ON communication.calls(is_spam, spam_score) WHERE is_spam = true;
CREATE INDEX IF NOT EXISTS idx_calls_user_date ON communication.calls(user_id, started_at);
CREATE INDEX IF NOT EXISTS idx_messages_user_id ON communication.messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_contact_id ON communication.messages(contact_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON communication.messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_phone_number ON communication.messages(phone_number);
CREATE INDEX IF NOT EXISTS idx_messages_received_at ON communication.messages(received_at);
CREATE INDEX IF NOT EXISTS idx_messages_direction ON communication.messages(direction);
CREATE INDEX IF NOT EXISTS idx_messages_unread ON communication.messages(user_id, is_read, received_at) WHERE is_read = false;
CREATE INDEX IF NOT EXISTS idx_messages_spam ON communication.messages(is_spam, spam_score) WHERE is_spam = true;
CREATE INDEX IF NOT EXISTS idx_messages_body_search ON communication.messages USING gin(to_tsvector('english', message_body));
CREATE INDEX IF NOT EXISTS idx_conversation_contexts_user_id ON communication.conversation_contexts(user_id);
CREATE INDEX IF NOT EXISTS idx_conversation_contexts_conversation_id ON communication.conversation_contexts(conversation_id);
CREATE INDEX IF NOT EXISTS idx_conversation_contexts_active ON communication.conversation_contexts(is_active, start_time) WHERE is_active = true;
