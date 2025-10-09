
-- =============================================
-- ANALYTICS & REPORTING SCHEMA
-- =============================================

CREATE TABLE IF NOT EXISTS analytics.weekly_reports (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES user_management.users(id) ON DELETE CASCADE,
    report_week DATE NOT NULL, -- Start of the week (Monday)
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_calls INTEGER DEFAULT 0 CHECK (total_calls >= 0),
    total_messages INTEGER DEFAULT 0 CHECK (total_messages >= 0),
    total_call_duration_seconds INTEGER DEFAULT 0 CHECK (total_call_duration_seconds >= 0),
    spam_calls_blocked INTEGER DEFAULT 0 CHECK (spam_calls_blocked >= 0),
    spam_messages_blocked INTEGER DEFAULT 0 CHECK (spam_messages_blocked >= 0),
    ai_interactions INTEGER DEFAULT 0 CHECK (ai_interactions >= 0),
    peak_call_hours JSONB DEFAULT '{}',
    top_contacts JSONB DEFAULT '[]',
    sentiment_summary JSONB DEFAULT '{}',
    average_call_duration DECIMAL(8,2) DEFAULT 0,
    busiest_day_of_week INTEGER CHECK (busiest_day_of_week BETWEEN 0 AND 6),
    total_ai_responses INTEGER DEFAULT 0,
    emergency_calls INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    
    CONSTRAINT weekly_reports_user_week_unique UNIQUE(user_id, report_week),
    CONSTRAINT weekly_reports_date_logic CHECK (end_date >= start_date),
    CONSTRAINT weekly_reports_week_alignment CHECK (EXTRACT(DOW FROM report_week) = 1) -- Monday = 1
);

CREATE TABLE IF NOT EXISTS analytics.monthly_reports (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES user_management.users(id) ON DELETE CASCADE,
    report_month DATE NOT NULL, -- First day of the month
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_calls INTEGER DEFAULT 0,
    total_messages INTEGER DEFAULT 0,
    total_call_duration_seconds INTEGER DEFAULT 0,
    spam_calls_blocked INTEGER DEFAULT 0,
    spam_messages_blocked INTEGER DEFAULT 0,
    ai_interactions INTEGER DEFAULT 0,
    most_contacted_numbers JSONB DEFAULT '[]',
    call_patterns JSONB DEFAULT '{}',
    message_patterns JSONB DEFAULT '{}',
    ai_effectiveness_score DECIMAL(3,2) CHECK (ai_effectiveness_score BETWEEN 0 AND 1),
    cost_savings_estimate DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    
    CONSTRAINT monthly_reports_user_month_unique UNIQUE(user_id, report_month)
);

CREATE TABLE IF NOT EXISTS analytics.user_activity_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES user_management.users(id) ON DELETE CASCADE,
    activity_type TEXT NOT NULL CHECK (activity_type IN ('login', 'logout', 'call_made', 'call_received', 'message_sent', 'message_received', 'ai_instruction_created', 'ai_instruction_updated', 'settings_changed', 'spam_reported', 'contact_added', 'contact_blocked')),
    activity_details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    session_id TEXT,
    duration_seconds INTEGER CHECK (duration_seconds >= 0),
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    
    CONSTRAINT user_activity_logs_session_check CHECK (session_id IS NOT NULL OR activity_type IN ('call_made', 'call_received', 'message_sent', 'message_received'))
);

CREATE TABLE IF NOT EXISTS analytics.call_analytics (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES user_management.users(id) ON DELETE CASCADE,
    call_id BIGINT NOT NULL REFERENCES communication.calls(id) ON DELETE CASCADE,
    analysis_type TEXT NOT NULL CHECK (analysis_type IN ('sentiment', 'intent', 'urgency', 'spam_detection', 'topic_extraction', 'emotion_detection', 'keyword_extraction')),
    analysis_result JSONB NOT NULL,
    confidence_score DECIMAL(3,2) CHECK (confidence_score BETWEEN 0 AND 1),
    model_used TEXT,
    processing_time_ms INTEGER CHECK (processing_time_ms >= 0),
    tokens_processed INTEGER CHECK (tokens_processed >= 0),
    cost_estimate DECIMAL(8,4) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    
    CONSTRAINT call_analytics_call_type_unique UNIQUE(call_id, analysis_type)
);

CREATE TABLE IF NOT EXISTS analytics.message_analytics (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES user_management.users(id) ON DELETE CASCADE,
    message_id BIGINT NOT NULL REFERENCES communication.messages(id) ON DELETE CASCADE,
    analysis_type TEXT NOT NULL CHECK (analysis_type IN ('sentiment', 'intent', 'spam_detection', 'topic_extraction', 'urgency', 'language_detection', 'entity_extraction')),
    analysis_result JSONB NOT NULL,
    confidence_score DECIMAL(3,2) CHECK (confidence_score BETWEEN 0 AND 1),
    model_used TEXT,
    processing_time_ms INTEGER CHECK (processing_time_ms >= 0),
    tokens_processed INTEGER CHECK (tokens_processed >= 0),
    cost_estimate DECIMAL(8,4) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    
    CONSTRAINT message_analytics_message_type_unique UNIQUE(message_id, analysis_type)
);

CREATE TABLE IF NOT EXISTS analytics.ai_performance_metrics (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES user_management.users(id) ON DELETE CASCADE,
    metric_date DATE NOT NULL DEFAULT CURRENT_DATE,
    metric_type TEXT NOT NULL CHECK (metric_type IN ('response_accuracy', 'response_time', 'user_satisfaction', 'spam_detection_accuracy', 'false_positive_rate', 'false_negative_rate')),
    metric_value DECIMAL(8,4) NOT NULL,
    sample_size INTEGER DEFAULT 1 CHECK (sample_size > 0),
    model_version TEXT,
    context_data JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    
    CONSTRAINT ai_performance_metrics_unique UNIQUE(user_id, metric_date, metric_type, model_version)
);

CREATE TABLE IF NOT EXISTS analytics.usage_statistics (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES user_management.users(id) ON DELETE CASCADE,
    stat_date DATE NOT NULL DEFAULT CURRENT_DATE,
    calls_handled_by_ai INTEGER DEFAULT 0,
    messages_processed INTEGER DEFAULT 0,
    spam_blocked INTEGER DEFAULT 0,
    ai_instructions_used INTEGER DEFAULT 0,
    voice_cloning_minutes INTEGER DEFAULT 0,
    transcription_minutes INTEGER DEFAULT 0,
    api_calls_made INTEGER DEFAULT 0,
    storage_used_mb DECIMAL(10,2) DEFAULT 0,
    bandwidth_used_mb DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    CONSTRAINT usage_statistics_user_date_unique UNIQUE(user_id, stat_date)
);

CREATE TABLE IF NOT EXISTS analytics.contact_interaction_summary (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES user_management.users(id) ON DELETE CASCADE,
    contact_id BIGINT NOT NULL REFERENCES user_management.contacts(id) ON DELETE CASCADE,
    summary_date DATE NOT NULL DEFAULT CURRENT_DATE,
    total_calls INTEGER DEFAULT 0,
    total_messages INTEGER DEFAULT 0,
    total_call_duration_seconds INTEGER DEFAULT 0,
    last_interaction_type TEXT CHECK (last_interaction_type IN ('call', 'message')),
    last_interaction_at TIMESTAMPTZ,
    interaction_frequency_score DECIMAL(3,2) DEFAULT 0 CHECK (interaction_frequency_score BETWEEN 0 AND 1),
    relationship_strength DECIMAL(3,2) DEFAULT 0 CHECK (relationship_strength BETWEEN 0 AND 1),
    avg_sentiment_score DECIMAL(3,2) CHECK (avg_sentiment_score BETWEEN -1 AND 1),
    spam_likelihood DECIMAL(3,2) DEFAULT 0 CHECK (spam_likelihood BETWEEN 0 AND 1),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    CONSTRAINT contact_interaction_summary_unique UNIQUE(user_id, contact_id, summary_date)
);

CREATE TABLE IF NOT EXISTS analytics.system_performance_logs (
    id BIGSERIAL PRIMARY KEY,
    log_timestamp TIMESTAMPTZ DEFAULT now(),
    component_name TEXT NOT NULL CHECK (component_name IN ('api_server', 'ai_processor', 'spam_detector', 'voice_synthesizer', 'transcription_service', 'database')),
    metric_type TEXT NOT NULL CHECK (metric_type IN ('response_time', 'cpu_usage', 'memory_usage', 'disk_usage', 'error_rate', 'throughput')),
    metric_value DECIMAL(10,4) NOT NULL,
    unit TEXT NOT NULL,
    server_instance TEXT,
    additional_data JSONB DEFAULT '{}',
    
    CONSTRAINT system_performance_logs_timestamp_component UNIQUE(log_timestamp, component_name, metric_type)
);

-- Indexes for analytics schema
CREATE INDEX IF NOT EXISTS idx_weekly_reports_user_week ON analytics.weekly_reports(user_id, report_week);
CREATE INDEX IF NOT EXISTS idx_weekly_reports_date_range ON analytics.weekly_reports(start_date, end_date);

CREATE INDEX IF NOT EXISTS idx_monthly_reports_user_month ON analytics.monthly_reports(user_id, report_month);
CREATE INDEX IF NOT EXISTS idx_monthly_reports_date_range ON analytics.monthly_reports(start_date, end_date);

CREATE INDEX IF NOT EXISTS idx_user_activity_logs_user_time ON analytics.user_activity_logs(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_type ON analytics.user_activity_logs(activity_type, created_at);
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_session ON analytics.user_activity_logs(session_id) WHERE session_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_ip ON analytics.user_activity_logs(ip_address, created_at);

CREATE INDEX IF NOT EXISTS idx_call_analytics_call_id ON analytics.call_analytics(call_id);
CREATE INDEX IF NOT EXISTS idx_call_analytics_user_type ON analytics.call_analytics(user_id, analysis_type);
CREATE INDEX IF NOT EXISTS idx_call_analytics_created ON analytics.call_analytics(created_at);

CREATE INDEX IF NOT EXISTS idx_message_analytics_message_id ON analytics.message_analytics(message_id);
CREATE INDEX IF NOT EXISTS idx_message_analytics_user_type ON analytics.message_analytics(user_id, analysis_type);
CREATE INDEX IF NOT EXISTS idx_message_analytics_created ON analytics.message_analytics(created_at);

CREATE INDEX IF NOT EXISTS idx_ai_performance_metrics_user_date ON analytics.ai_performance_metrics(user_id, metric_date);
CREATE INDEX IF NOT EXISTS idx_ai_performance_metrics_type ON analytics.ai_performance_metrics(metric_type, metric_date);

CREATE INDEX IF NOT EXISTS idx_usage_statistics_user_date ON analytics.usage_statistics(user_id, stat_date);
CREATE INDEX IF NOT EXISTS idx_usage_statistics_date ON analytics.usage_statistics(stat_date);

CREATE INDEX IF NOT EXISTS idx_contact_interaction_summary_user_contact ON analytics.contact_interaction_summary(user_id, contact_id);
