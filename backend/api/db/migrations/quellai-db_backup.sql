--
-- PostgreSQL database dump
--

\restrict sBOhVppb0fGs7FssoclB9eiNpCdVaxntQ0ec8xkQBQN8ya9eXZipuvOKaBBkh6h

-- Dumped from database version 17.6 (Debian 17.6-1.pgdg12+1)
-- Dumped by pg_dump version 17.6 (Debian 17.6-1.pgdg12+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
-- SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: ai_intelligence; Type: SCHEMA; Schema: -; Owner: user_ai
--

CREATE SCHEMA ai_intelligence;


ALTER SCHEMA ai_intelligence OWNER TO user_ai;

--
-- Name: analytics; Type: SCHEMA; Schema: -; Owner: user_ai
--

CREATE SCHEMA analytics;


ALTER SCHEMA analytics OWNER TO user_ai;

--
-- Name: communication; Type: SCHEMA; Schema: -; Owner: user_ai
--

CREATE SCHEMA communication;


ALTER SCHEMA communication OWNER TO user_ai;

--
-- Name: data_feeds; Type: SCHEMA; Schema: -; Owner: user_ai
--

CREATE SCHEMA data_feeds;


ALTER SCHEMA data_feeds OWNER TO user_ai;

--
-- Name: SCHEMA data_feeds; Type: COMMENT; Schema: -; Owner: user_ai
--

COMMENT ON SCHEMA data_feeds IS 'Schema for data feeds input files and related tables';


--
-- Name: data_feeds_metadata; Type: SCHEMA; Schema: -; Owner: user_ai
--

CREATE SCHEMA data_feeds_metadata;


ALTER SCHEMA data_feeds_metadata OWNER TO user_ai;

--
-- Name: SCHEMA data_feeds_metadata; Type: COMMENT; Schema: -; Owner: user_ai
--

COMMENT ON SCHEMA data_feeds_metadata IS 'Schema for extracted metadata, concepts, and mappings';


--
-- Name: data_feeds_vectors; Type: SCHEMA; Schema: -; Owner: user_ai
--

CREATE SCHEMA data_feeds_vectors;


ALTER SCHEMA data_feeds_vectors OWNER TO user_ai;

--
-- Name: SCHEMA data_feeds_vectors; Type: COMMENT; Schema: -; Owner: user_ai
--

COMMENT ON SCHEMA data_feeds_vectors IS 'Schema for vector embeddings storage';



--
-- Name: user_management; Type: SCHEMA; Schema: -; Owner: user_ai
--

CREATE SCHEMA user_management;


ALTER SCHEMA user_management OWNER TO user_ai;

--
-- Name: pg_trgm; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;


--
-- Name: EXTENSION pg_trgm; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pg_trgm IS 'text similarity measurement and index searching based on trigrams';


--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: vector; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;


--
-- Name: EXTENSION vector; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION vector IS 'vector data type and ivfflat and hnsw access methods';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: ai_instructions; Type: TABLE; Schema: ai_intelligence; Owner: user_ai
--

CREATE TABLE ai_intelligence.ai_instructions (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    title character varying(200) NOT NULL,
    instruction_text text NOT NULL,
    instruction_type character varying(50) DEFAULT 'general'::character varying,
    context_type character varying(20) DEFAULT 'all'::character varying,
    channel character varying(50),
    target_identifier character varying(255),
    context_tags jsonb,
    priority character varying(10) DEFAULT 'normal'::character varying,
    priority_weight integer DEFAULT 0,
    status character varying(20) DEFAULT 'active'::character varying,
    verification_required boolean DEFAULT false,
    verification_method character varying(50),
    verification_data jsonb,
    usage_count integer DEFAULT 0,
    max_usage integer,
    last_triggered_at timestamp with time zone,
    expires_at timestamp with time zone,
    auto_archive_at timestamp with time zone,
    completed_at timestamp with time zone,
    archived_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE ai_intelligence.ai_instructions OWNER TO user_ai;

--
-- Name: ai_instructions_id_seq; Type: SEQUENCE; Schema: ai_intelligence; Owner: user_ai
--

CREATE SEQUENCE ai_intelligence.ai_instructions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE ai_intelligence.ai_instructions_id_seq OWNER TO user_ai;

--
-- Name: ai_instructions_id_seq; Type: SEQUENCE OWNED BY; Schema: ai_intelligence; Owner: user_ai
--

ALTER SEQUENCE ai_intelligence.ai_instructions_id_seq OWNED BY ai_intelligence.ai_instructions.id;


--
-- Name: embeddings; Type: TABLE; Schema: ai_intelligence; Owner: user_ai
--

CREATE TABLE ai_intelligence.embeddings (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    content_type text NOT NULL,
    content_id bigint NOT NULL,
    content_text text NOT NULL,
    embedding public.vector(384) NOT NULL,
    model_name text DEFAULT 'sentence-transformers/all-MiniLM-L6-v2'::text NOT NULL,
    model_version text DEFAULT '1.0'::text,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT embeddings_content_not_empty CHECK ((char_length(TRIM(BOTH FROM content_text)) > 0)),
    CONSTRAINT embeddings_content_type_check CHECK ((content_type = ANY (ARRAY['feed_item'::text, 'policy'::text, 'call_transcript'::text, 'message'::text, 'document'::text])))
);


ALTER TABLE ai_intelligence.embeddings OWNER TO user_ai;

--
-- Name: embeddings_id_seq; Type: SEQUENCE; Schema: ai_intelligence; Owner: user_ai
--

CREATE SEQUENCE ai_intelligence.embeddings_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE ai_intelligence.embeddings_id_seq OWNER TO user_ai;

--
-- Name: embeddings_id_seq; Type: SEQUENCE OWNED BY; Schema: ai_intelligence; Owner: user_ai
--

ALTER SEQUENCE ai_intelligence.embeddings_id_seq OWNED BY ai_intelligence.embeddings.id;


--
-- Name: feed_items; Type: TABLE; Schema: ai_intelligence; Owner: user_ai
--

CREATE TABLE ai_intelligence.feed_items (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    title text NOT NULL,
    body text NOT NULL,
    tags text[] DEFAULT '{}'::text[],
    priority integer DEFAULT 0,
    status text DEFAULT 'active'::text,
    is_sensitive boolean DEFAULT false,
    embedding public.vector(384),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    expires_at timestamp with time zone DEFAULT (now() + '7 days'::interval),
    last_accessed_at timestamp with time zone,
    CONSTRAINT feed_items_body_not_empty CHECK ((char_length(TRIM(BOTH FROM body)) > 0)),
    CONSTRAINT feed_items_expires_future CHECK ((expires_at > created_at)),
    CONSTRAINT feed_items_priority_check CHECK (((priority >= 0) AND (priority <= 10))),
    CONSTRAINT feed_items_status_check CHECK ((status = ANY (ARRAY['active'::text, 'archived'::text, 'expired'::text]))),
    CONSTRAINT feed_items_title_not_empty CHECK ((char_length(TRIM(BOTH FROM title)) > 0))
);


ALTER TABLE ai_intelligence.feed_items OWNER TO user_ai;

--
-- Name: feed_items_id_seq; Type: SEQUENCE; Schema: ai_intelligence; Owner: user_ai
--

CREATE SEQUENCE ai_intelligence.feed_items_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE ai_intelligence.feed_items_id_seq OWNER TO user_ai;

--
-- Name: feed_items_id_seq; Type: SEQUENCE OWNED BY; Schema: ai_intelligence; Owner: user_ai
--

ALTER SEQUENCE ai_intelligence.feed_items_id_seq OWNED BY ai_intelligence.feed_items.id;


--
-- Name: labs_images; Type: TABLE; Schema: ai_intelligence; Owner: user_ai
--

CREATE TABLE ai_intelligence.labs_images (
    image_id uuid NOT NULL,
    convo_id uuid,
    user_id bigint,
    url text,
    caption text,
    embedding public.vector(1536),
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE ai_intelligence.labs_images OWNER TO user_ai;

--
-- Name: labs_message_chunks; Type: TABLE; Schema: ai_intelligence; Owner: user_ai
--

CREATE TABLE ai_intelligence.labs_message_chunks (
    chunk_id uuid NOT NULL,
    message_id uuid,
    ord integer,
    text text NOT NULL,
    embedding public.vector(1536)
);


ALTER TABLE ai_intelligence.labs_message_chunks OWNER TO user_ai;

--
-- Name: labs_messages; Type: TABLE; Schema: ai_intelligence; Owner: user_ai
--

CREATE TABLE ai_intelligence.labs_messages (
    message_id uuid NOT NULL,
    convo_id uuid,
    user_id bigint,
    source_lang text,
    target_lang text,
    raw_text text NOT NULL,
    final_summary text,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE ai_intelligence.labs_messages OWNER TO user_ai;

--
-- Name: ml_model_metrics; Type: TABLE; Schema: ai_intelligence; Owner: user_ai
--

CREATE TABLE ai_intelligence.ml_model_metrics (
    id bigint NOT NULL,
    model_name text NOT NULL,
    model_version text NOT NULL,
    metric_type text NOT NULL,
    metric_value numeric(5,4) NOT NULL,
    dataset_size integer NOT NULL,
    evaluation_date timestamp with time zone DEFAULT now(),
    metadata jsonb DEFAULT '{}'::jsonb,
    CONSTRAINT ml_model_metrics_dataset_size_check CHECK ((dataset_size > 0)),
    CONSTRAINT ml_model_metrics_metric_type_check CHECK ((metric_type = ANY (ARRAY['accuracy'::text, 'precision'::text, 'recall'::text, 'f1_score'::text, 'auc_roc'::text]))),
    CONSTRAINT ml_model_metrics_metric_value_check CHECK (((metric_value >= (0)::numeric) AND (metric_value <= (1)::numeric)))
);


ALTER TABLE ai_intelligence.ml_model_metrics OWNER TO user_ai;

--
-- Name: ml_model_metrics_id_seq; Type: SEQUENCE; Schema: ai_intelligence; Owner: user_ai
--

CREATE SEQUENCE ai_intelligence.ml_model_metrics_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE ai_intelligence.ml_model_metrics_id_seq OWNER TO user_ai;

--
-- Name: ml_model_metrics_id_seq; Type: SEQUENCE OWNED BY; Schema: ai_intelligence; Owner: user_ai
--

ALTER SEQUENCE ai_intelligence.ml_model_metrics_id_seq OWNED BY ai_intelligence.ml_model_metrics.id;


--
-- Name: policies; Type: TABLE; Schema: ai_intelligence; Owner: user_ai
--

CREATE TABLE ai_intelligence.policies (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    title text NOT NULL,
    body_text text NOT NULL,
    policy_type text DEFAULT 'general'::text,
    tags text[] DEFAULT '{}'::text[],
    is_active boolean DEFAULT true,
    priority integer DEFAULT 0,
    embedding public.vector(384),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT policies_body_not_empty CHECK ((char_length(TRIM(BOTH FROM body_text)) > 0)),
    CONSTRAINT policies_policy_type_check CHECK ((policy_type = ANY (ARRAY['general'::text, 'spam'::text, 'emergency'::text, 'business'::text, 'personal'::text]))),
    CONSTRAINT policies_priority_check CHECK (((priority >= 0) AND (priority <= 10))),
    CONSTRAINT policies_title_not_empty CHECK ((char_length(TRIM(BOTH FROM title)) > 0))
);


ALTER TABLE ai_intelligence.policies OWNER TO user_ai;

--
-- Name: policies_id_seq; Type: SEQUENCE; Schema: ai_intelligence; Owner: user_ai
--

CREATE SEQUENCE ai_intelligence.policies_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE ai_intelligence.policies_id_seq OWNER TO user_ai;

--
-- Name: policies_id_seq; Type: SEQUENCE OWNED BY; Schema: ai_intelligence; Owner: user_ai
--

ALTER SEQUENCE ai_intelligence.policies_id_seq OWNED BY ai_intelligence.policies.id;


--
-- Name: spam_patterns; Type: TABLE; Schema: ai_intelligence; Owner: user_ai
--

CREATE TABLE ai_intelligence.spam_patterns (
    id bigint NOT NULL,
    pattern_type text NOT NULL,
    pattern_value text NOT NULL,
    confidence_score numeric(3,2) NOT NULL,
    is_active boolean DEFAULT true,
    source text DEFAULT 'system'::text,
    created_by bigint,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT spam_patterns_confidence_score_check CHECK (((confidence_score >= (0)::numeric) AND (confidence_score <= (1)::numeric))),
    CONSTRAINT spam_patterns_pattern_type_check CHECK ((pattern_type = ANY (ARRAY['keyword'::text, 'phone_pattern'::text, 'content_pattern'::text, 'behavioral'::text]))),
    CONSTRAINT spam_patterns_source_check CHECK ((source = ANY (ARRAY['system'::text, 'user'::text, 'community'::text, 'ml_model'::text]))),
    CONSTRAINT spam_patterns_value_not_empty CHECK ((char_length(TRIM(BOTH FROM pattern_value)) > 0))
);


ALTER TABLE ai_intelligence.spam_patterns OWNER TO user_ai;

--
-- Name: spam_patterns_id_seq; Type: SEQUENCE; Schema: ai_intelligence; Owner: user_ai
--

CREATE SEQUENCE ai_intelligence.spam_patterns_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE ai_intelligence.spam_patterns_id_seq OWNER TO user_ai;

--
-- Name: spam_patterns_id_seq; Type: SEQUENCE OWNED BY; Schema: ai_intelligence; Owner: user_ai
--

ALTER SEQUENCE ai_intelligence.spam_patterns_id_seq OWNED BY ai_intelligence.spam_patterns.id;


--
-- Name: voice_models; Type: TABLE; Schema: ai_intelligence; Owner: user_ai
--

CREATE TABLE ai_intelligence.voice_models (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    model_name text NOT NULL,
    voice_sample_uri text,
    model_uri text,
    training_status text DEFAULT 'pending'::text,
    quality_score numeric(3,2),
    is_active boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT voice_models_quality_score_check CHECK (((quality_score >= (0)::numeric) AND (quality_score <= (1)::numeric))),
    CONSTRAINT voice_models_training_status_check CHECK ((training_status = ANY (ARRAY['pending'::text, 'training'::text, 'completed'::text, 'failed'::text])))
);


ALTER TABLE ai_intelligence.voice_models OWNER TO user_ai;

--
-- Name: voice_models_id_seq; Type: SEQUENCE; Schema: ai_intelligence; Owner: user_ai
--

CREATE SEQUENCE ai_intelligence.voice_models_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE ai_intelligence.voice_models_id_seq OWNER TO user_ai;

--
-- Name: voice_models_id_seq; Type: SEQUENCE OWNED BY; Schema: ai_intelligence; Owner: user_ai
--

ALTER SEQUENCE ai_intelligence.voice_models_id_seq OWNED BY ai_intelligence.voice_models.id;


--
-- Name: ai_performance_metrics; Type: TABLE; Schema: analytics; Owner: user_ai
--

CREATE TABLE analytics.ai_performance_metrics (
    id bigint NOT NULL,
    user_id bigint,
    metric_date date DEFAULT CURRENT_DATE NOT NULL,
    metric_type text NOT NULL,
    metric_value numeric(8,4) NOT NULL,
    sample_size integer DEFAULT 1,
    model_version text,
    context_data jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT ai_performance_metrics_metric_type_check CHECK ((metric_type = ANY (ARRAY['response_accuracy'::text, 'response_time'::text, 'user_satisfaction'::text, 'spam_detection_accuracy'::text, 'false_positive_rate'::text, 'false_negative_rate'::text]))),
    CONSTRAINT ai_performance_metrics_sample_size_check CHECK ((sample_size > 0))
);


ALTER TABLE analytics.ai_performance_metrics OWNER TO user_ai;

--
-- Name: ai_performance_metrics_id_seq; Type: SEQUENCE; Schema: analytics; Owner: user_ai
--

CREATE SEQUENCE analytics.ai_performance_metrics_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE analytics.ai_performance_metrics_id_seq OWNER TO user_ai;

--
-- Name: ai_performance_metrics_id_seq; Type: SEQUENCE OWNED BY; Schema: analytics; Owner: user_ai
--

ALTER SEQUENCE analytics.ai_performance_metrics_id_seq OWNED BY analytics.ai_performance_metrics.id;


--
-- Name: call_analytics; Type: TABLE; Schema: analytics; Owner: user_ai
--

CREATE TABLE analytics.call_analytics (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    call_id bigint NOT NULL,
    analysis_type text NOT NULL,
    analysis_result jsonb NOT NULL,
    confidence_score numeric(3,2),
    model_used text,
    processing_time_ms integer,
    tokens_processed integer,
    cost_estimate numeric(8,4) DEFAULT 0,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT call_analytics_analysis_type_check CHECK ((analysis_type = ANY (ARRAY['sentiment'::text, 'intent'::text, 'urgency'::text, 'spam_detection'::text, 'topic_extraction'::text, 'emotion_detection'::text, 'keyword_extraction'::text]))),
    CONSTRAINT call_analytics_confidence_score_check CHECK (((confidence_score >= (0)::numeric) AND (confidence_score <= (1)::numeric))),
    CONSTRAINT call_analytics_processing_time_ms_check CHECK ((processing_time_ms >= 0)),
    CONSTRAINT call_analytics_tokens_processed_check CHECK ((tokens_processed >= 0))
);


ALTER TABLE analytics.call_analytics OWNER TO user_ai;

--
-- Name: call_analytics_id_seq; Type: SEQUENCE; Schema: analytics; Owner: user_ai
--

CREATE SEQUENCE analytics.call_analytics_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE analytics.call_analytics_id_seq OWNER TO user_ai;

--
-- Name: call_analytics_id_seq; Type: SEQUENCE OWNED BY; Schema: analytics; Owner: user_ai
--

ALTER SEQUENCE analytics.call_analytics_id_seq OWNED BY analytics.call_analytics.id;


--
-- Name: contact_interaction_summary; Type: TABLE; Schema: analytics; Owner: user_ai
--

CREATE TABLE analytics.contact_interaction_summary (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    contact_id bigint NOT NULL,
    summary_date date DEFAULT CURRENT_DATE NOT NULL,
    total_calls integer DEFAULT 0,
    total_messages integer DEFAULT 0,
    total_call_duration_seconds integer DEFAULT 0,
    last_interaction_type text,
    last_interaction_at timestamp with time zone,
    interaction_frequency_score numeric(3,2) DEFAULT 0,
    relationship_strength numeric(3,2) DEFAULT 0,
    avg_sentiment_score numeric(3,2),
    spam_likelihood numeric(3,2) DEFAULT 0,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT contact_interaction_summary_avg_sentiment_score_check CHECK (((avg_sentiment_score >= ('-1'::integer)::numeric) AND (avg_sentiment_score <= (1)::numeric))),
    CONSTRAINT contact_interaction_summary_interaction_frequency_score_check CHECK (((interaction_frequency_score >= (0)::numeric) AND (interaction_frequency_score <= (1)::numeric))),
    CONSTRAINT contact_interaction_summary_last_interaction_type_check CHECK ((last_interaction_type = ANY (ARRAY['call'::text, 'message'::text]))),
    CONSTRAINT contact_interaction_summary_relationship_strength_check CHECK (((relationship_strength >= (0)::numeric) AND (relationship_strength <= (1)::numeric))),
    CONSTRAINT contact_interaction_summary_spam_likelihood_check CHECK (((spam_likelihood >= (0)::numeric) AND (spam_likelihood <= (1)::numeric)))
);


ALTER TABLE analytics.contact_interaction_summary OWNER TO user_ai;

--
-- Name: contact_interaction_summary_id_seq; Type: SEQUENCE; Schema: analytics; Owner: user_ai
--

CREATE SEQUENCE analytics.contact_interaction_summary_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE analytics.contact_interaction_summary_id_seq OWNER TO user_ai;

--
-- Name: contact_interaction_summary_id_seq; Type: SEQUENCE OWNED BY; Schema: analytics; Owner: user_ai
--

ALTER SEQUENCE analytics.contact_interaction_summary_id_seq OWNED BY analytics.contact_interaction_summary.id;


--
-- Name: message_analytics; Type: TABLE; Schema: analytics; Owner: user_ai
--

CREATE TABLE analytics.message_analytics (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    message_id bigint NOT NULL,
    analysis_type text NOT NULL,
    analysis_result jsonb NOT NULL,
    confidence_score numeric(3,2),
    model_used text,
    processing_time_ms integer,
    tokens_processed integer,
    cost_estimate numeric(8,4) DEFAULT 0,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT message_analytics_analysis_type_check CHECK ((analysis_type = ANY (ARRAY['sentiment'::text, 'intent'::text, 'spam_detection'::text, 'topic_extraction'::text, 'urgency'::text, 'language_detection'::text, 'entity_extraction'::text]))),
    CONSTRAINT message_analytics_confidence_score_check CHECK (((confidence_score >= (0)::numeric) AND (confidence_score <= (1)::numeric))),
    CONSTRAINT message_analytics_processing_time_ms_check CHECK ((processing_time_ms >= 0)),
    CONSTRAINT message_analytics_tokens_processed_check CHECK ((tokens_processed >= 0))
);


ALTER TABLE analytics.message_analytics OWNER TO user_ai;

--
-- Name: message_analytics_id_seq; Type: SEQUENCE; Schema: analytics; Owner: user_ai
--

CREATE SEQUENCE analytics.message_analytics_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE analytics.message_analytics_id_seq OWNER TO user_ai;

--
-- Name: message_analytics_id_seq; Type: SEQUENCE OWNED BY; Schema: analytics; Owner: user_ai
--

ALTER SEQUENCE analytics.message_analytics_id_seq OWNED BY analytics.message_analytics.id;


--
-- Name: monthly_reports; Type: TABLE; Schema: analytics; Owner: user_ai
--

CREATE TABLE analytics.monthly_reports (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    report_month date NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    total_calls integer DEFAULT 0,
    total_messages integer DEFAULT 0,
    total_call_duration_seconds integer DEFAULT 0,
    spam_calls_blocked integer DEFAULT 0,
    spam_messages_blocked integer DEFAULT 0,
    ai_interactions integer DEFAULT 0,
    most_contacted_numbers jsonb DEFAULT '[]'::jsonb,
    call_patterns jsonb DEFAULT '{}'::jsonb,
    message_patterns jsonb DEFAULT '{}'::jsonb,
    ai_effectiveness_score numeric(3,2),
    cost_savings_estimate numeric(10,2) DEFAULT 0,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT monthly_reports_ai_effectiveness_score_check CHECK (((ai_effectiveness_score >= (0)::numeric) AND (ai_effectiveness_score <= (1)::numeric)))
);


ALTER TABLE analytics.monthly_reports OWNER TO user_ai;

--
-- Name: monthly_reports_id_seq; Type: SEQUENCE; Schema: analytics; Owner: user_ai
--

CREATE SEQUENCE analytics.monthly_reports_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE analytics.monthly_reports_id_seq OWNER TO user_ai;

--
-- Name: monthly_reports_id_seq; Type: SEQUENCE OWNED BY; Schema: analytics; Owner: user_ai
--

ALTER SEQUENCE analytics.monthly_reports_id_seq OWNED BY analytics.monthly_reports.id;


--
-- Name: system_performance_logs; Type: TABLE; Schema: analytics; Owner: user_ai
--

CREATE TABLE analytics.system_performance_logs (
    id bigint NOT NULL,
    log_timestamp timestamp with time zone DEFAULT now(),
    component_name text NOT NULL,
    metric_type text NOT NULL,
    metric_value numeric(10,4) NOT NULL,
    unit text NOT NULL,
    server_instance text,
    additional_data jsonb DEFAULT '{}'::jsonb,
    CONSTRAINT system_performance_logs_component_name_check CHECK ((component_name = ANY (ARRAY['api_server'::text, 'ai_processor'::text, 'spam_detector'::text, 'voice_synthesizer'::text, 'transcription_service'::text, 'database'::text]))),
    CONSTRAINT system_performance_logs_metric_type_check CHECK ((metric_type = ANY (ARRAY['response_time'::text, 'cpu_usage'::text, 'memory_usage'::text, 'disk_usage'::text, 'error_rate'::text, 'throughput'::text])))
);


ALTER TABLE analytics.system_performance_logs OWNER TO user_ai;

--
-- Name: system_performance_logs_id_seq; Type: SEQUENCE; Schema: analytics; Owner: user_ai
--

CREATE SEQUENCE analytics.system_performance_logs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE analytics.system_performance_logs_id_seq OWNER TO user_ai;

--
-- Name: system_performance_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: analytics; Owner: user_ai
--

ALTER SEQUENCE analytics.system_performance_logs_id_seq OWNED BY analytics.system_performance_logs.id;


--
-- Name: usage_statistics; Type: TABLE; Schema: analytics; Owner: user_ai
--

CREATE TABLE analytics.usage_statistics (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    stat_date date DEFAULT CURRENT_DATE NOT NULL,
    calls_handled_by_ai integer DEFAULT 0,
    messages_processed integer DEFAULT 0,
    spam_blocked integer DEFAULT 0,
    ai_instructions_used integer DEFAULT 0,
    voice_cloning_minutes integer DEFAULT 0,
    transcription_minutes integer DEFAULT 0,
    api_calls_made integer DEFAULT 0,
    storage_used_mb numeric(10,2) DEFAULT 0,
    bandwidth_used_mb numeric(10,2) DEFAULT 0,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE analytics.usage_statistics OWNER TO user_ai;

--
-- Name: usage_statistics_id_seq; Type: SEQUENCE; Schema: analytics; Owner: user_ai
--

CREATE SEQUENCE analytics.usage_statistics_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE analytics.usage_statistics_id_seq OWNER TO user_ai;

--
-- Name: usage_statistics_id_seq; Type: SEQUENCE OWNED BY; Schema: analytics; Owner: user_ai
--

ALTER SEQUENCE analytics.usage_statistics_id_seq OWNED BY analytics.usage_statistics.id;


--
-- Name: user_activity_logs; Type: TABLE; Schema: analytics; Owner: user_ai
--

CREATE TABLE analytics.user_activity_logs (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    activity_type text NOT NULL,
    activity_details jsonb DEFAULT '{}'::jsonb,
    ip_address inet,
    user_agent text,
    session_id text,
    duration_seconds integer,
    success boolean DEFAULT true,
    error_message text,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT user_activity_logs_activity_type_check CHECK ((activity_type = ANY (ARRAY['login'::text, 'logout'::text, 'call_made'::text, 'call_received'::text, 'message_sent'::text, 'message_received'::text, 'ai_instruction_created'::text, 'ai_instruction_updated'::text, 'settings_changed'::text, 'spam_reported'::text, 'contact_added'::text, 'contact_blocked'::text]))),
    CONSTRAINT user_activity_logs_duration_seconds_check CHECK ((duration_seconds >= 0)),
    CONSTRAINT user_activity_logs_session_check CHECK (((session_id IS NOT NULL) OR (activity_type = ANY (ARRAY['call_made'::text, 'call_received'::text, 'message_sent'::text, 'message_received'::text]))))
);


ALTER TABLE analytics.user_activity_logs OWNER TO user_ai;

--
-- Name: user_activity_logs_id_seq; Type: SEQUENCE; Schema: analytics; Owner: user_ai
--

CREATE SEQUENCE analytics.user_activity_logs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE analytics.user_activity_logs_id_seq OWNER TO user_ai;

--
-- Name: user_activity_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: analytics; Owner: user_ai
--

ALTER SEQUENCE analytics.user_activity_logs_id_seq OWNED BY analytics.user_activity_logs.id;


--
-- Name: weekly_reports; Type: TABLE; Schema: analytics; Owner: user_ai
--

CREATE TABLE analytics.weekly_reports (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    report_week date NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    total_calls integer DEFAULT 0,
    total_messages integer DEFAULT 0,
    total_call_duration_seconds integer DEFAULT 0,
    spam_calls_blocked integer DEFAULT 0,
    spam_messages_blocked integer DEFAULT 0,
    ai_interactions integer DEFAULT 0,
    peak_call_hours jsonb DEFAULT '{}'::jsonb,
    top_contacts jsonb DEFAULT '[]'::jsonb,
    sentiment_summary jsonb DEFAULT '{}'::jsonb,
    average_call_duration numeric(8,2) DEFAULT 0,
    busiest_day_of_week integer,
    total_ai_responses integer DEFAULT 0,
    emergency_calls integer DEFAULT 0,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT weekly_reports_ai_interactions_check CHECK ((ai_interactions >= 0)),
    CONSTRAINT weekly_reports_busiest_day_of_week_check CHECK (((busiest_day_of_week >= 0) AND (busiest_day_of_week <= 6))),
    CONSTRAINT weekly_reports_date_logic CHECK ((end_date >= start_date)),
    CONSTRAINT weekly_reports_spam_calls_blocked_check CHECK ((spam_calls_blocked >= 0)),
    CONSTRAINT weekly_reports_spam_messages_blocked_check CHECK ((spam_messages_blocked >= 0)),
    CONSTRAINT weekly_reports_total_call_duration_seconds_check CHECK ((total_call_duration_seconds >= 0)),
    CONSTRAINT weekly_reports_total_calls_check CHECK ((total_calls >= 0)),
    CONSTRAINT weekly_reports_total_messages_check CHECK ((total_messages >= 0)),
    CONSTRAINT weekly_reports_week_alignment CHECK ((EXTRACT(dow FROM report_week) = (1)::numeric))
);


ALTER TABLE analytics.weekly_reports OWNER TO user_ai;

--
-- Name: weekly_reports_id_seq; Type: SEQUENCE; Schema: analytics; Owner: user_ai
--

CREATE SEQUENCE analytics.weekly_reports_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE analytics.weekly_reports_id_seq OWNER TO user_ai;

--
-- Name: weekly_reports_id_seq; Type: SEQUENCE OWNED BY; Schema: analytics; Owner: user_ai
--

ALTER SEQUENCE analytics.weekly_reports_id_seq OWNED BY analytics.weekly_reports.id;


--
-- Name: calls; Type: TABLE; Schema: communication; Owner: user_ai
--

CREATE TABLE communication.calls (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    contact_id bigint,
    from_number text NOT NULL,
    to_number text NOT NULL,
    direction text NOT NULL,
    status text DEFAULT 'pending'::text NOT NULL,
    started_at timestamp with time zone DEFAULT now(),
    answered_at timestamp with time zone,
    ended_at timestamp with time zone,
    duration_seconds integer DEFAULT 0,
    intent text,
    urgency text,
    outcome text,
    transcript text,
    transcript_confidence numeric(3,2),
    recording_uri text,
    recording_duration_seconds integer,
    spam_score integer DEFAULT 0,
    is_spam boolean DEFAULT false,
    ai_handled boolean DEFAULT false,
    policy_ids bigint[],
    metadata jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT calls_answered_logical CHECK (((answered_at IS NULL) OR (answered_at >= started_at))),
    CONSTRAINT calls_direction_check CHECK ((direction = ANY (ARRAY['incoming'::text, 'outgoing'::text]))),
    CONSTRAINT calls_duration_logical CHECK (((ended_at IS NULL) OR (answered_at IS NULL) OR (ended_at >= answered_at))),
    CONSTRAINT calls_duration_seconds_check CHECK ((duration_seconds >= 0)),
    CONSTRAINT calls_phone_format_from CHECK ((from_number ~ '^\+?[1-9]\d{1,14}'::text)),
    CONSTRAINT calls_phone_format_to CHECK ((to_number ~ '^\+?[1-9]\d{1,14}'::text)),
    CONSTRAINT calls_recording_duration_seconds_check CHECK ((recording_duration_seconds >= 0)),
    CONSTRAINT calls_spam_score_check CHECK (((spam_score >= 0) AND (spam_score <= 100))),
    CONSTRAINT calls_status_check CHECK ((status = ANY (ARRAY['pending'::text, 'ringing'::text, 'answered'::text, 'completed'::text, 'failed'::text, 'busy'::text, 'no_answer'::text]))),
    CONSTRAINT calls_transcript_confidence_check CHECK (((transcript_confidence >= (0)::numeric) AND (transcript_confidence <= (1)::numeric))),
    CONSTRAINT calls_urgency_check CHECK ((urgency = ANY (ARRAY['low'::text, 'medium'::text, 'high'::text, 'urgent'::text])))
);


ALTER TABLE communication.calls OWNER TO user_ai;

--
-- Name: calls_id_seq; Type: SEQUENCE; Schema: communication; Owner: user_ai
--

CREATE SEQUENCE communication.calls_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE communication.calls_id_seq OWNER TO user_ai;

--
-- Name: calls_id_seq; Type: SEQUENCE OWNED BY; Schema: communication; Owner: user_ai
--

ALTER SEQUENCE communication.calls_id_seq OWNED BY communication.calls.id;


--
-- Name: conversation_contexts; Type: TABLE; Schema: communication; Owner: user_ai
--

CREATE TABLE communication.conversation_contexts (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    conversation_id uuid NOT NULL,
    context_type text NOT NULL,
    summary text,
    key_topics text[],
    sentiment_analysis jsonb,
    participant_count integer DEFAULT 2,
    start_time timestamp with time zone NOT NULL,
    end_time timestamp with time zone,
    is_active boolean DEFAULT true,
    metadata jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT conversation_contexts_context_type_check CHECK ((context_type = ANY (ARRAY['call'::text, 'message_thread'::text, 'mixed'::text]))),
    CONSTRAINT conversation_contexts_participant_count_check CHECK ((participant_count >= 2)),
    CONSTRAINT conversation_contexts_start_time_logic CHECK (((end_time IS NULL) OR (start_time <= end_time))),
    CONSTRAINT conversation_contexts_time_logic CHECK (((end_time IS NULL) OR (end_time >= start_time)))
);


ALTER TABLE communication.conversation_contexts OWNER TO user_ai;

--
-- Name: conversation_contexts_id_seq; Type: SEQUENCE; Schema: communication; Owner: user_ai
--

CREATE SEQUENCE communication.conversation_contexts_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE communication.conversation_contexts_id_seq OWNER TO user_ai;

--
-- Name: conversation_contexts_id_seq; Type: SEQUENCE OWNED BY; Schema: communication; Owner: user_ai
--

ALTER SEQUENCE communication.conversation_contexts_id_seq OWNED BY communication.conversation_contexts.id;


--
-- Name: messages; Type: TABLE; Schema: communication; Owner: user_ai
--

CREATE TABLE communication.messages (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    contact_id bigint,
    conversation_id uuid DEFAULT public.uuid_generate_v4(),
    phone_number text NOT NULL,
    direction text NOT NULL,
    message_body text NOT NULL,
    message_type text DEFAULT 'text'::text,
    status text DEFAULT 'pending'::text,
    is_spam boolean DEFAULT false,
    spam_score integer DEFAULT 0,
    is_read boolean DEFAULT false,
    intent text,
    sentiment text,
    ai_response text,
    media_urls text[],
    metadata jsonb DEFAULT '{}'::jsonb,
    sent_at timestamp with time zone,
    received_at timestamp with time zone DEFAULT now(),
    read_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT messages_body_not_empty CHECK ((char_length(TRIM(BOTH FROM message_body)) > 0)),
    CONSTRAINT messages_direction_check CHECK ((direction = ANY (ARRAY['incoming'::text, 'outgoing'::text]))),
    CONSTRAINT messages_message_type_check CHECK ((message_type = ANY (ARRAY['text'::text, 'media'::text, 'location'::text, 'contact'::text]))),
    CONSTRAINT messages_phone_format CHECK ((phone_number ~ '^\+?[1-9]\d{1,14}'::text)),
    CONSTRAINT messages_read_logic CHECK (((is_read = false) OR (read_at IS NOT NULL))),
    CONSTRAINT messages_sentiment_check CHECK ((sentiment = ANY (ARRAY['positive'::text, 'negative'::text, 'neutral'::text]))),
    CONSTRAINT messages_spam_score_check CHECK (((spam_score >= 0) AND (spam_score <= 100))),
    CONSTRAINT messages_status_check CHECK ((status = ANY (ARRAY['pending'::text, 'sent'::text, 'delivered'::text, 'read'::text, 'failed'::text])))
);


ALTER TABLE communication.messages OWNER TO user_ai;

--
-- Name: messages_id_seq; Type: SEQUENCE; Schema: communication; Owner: user_ai
--

CREATE SEQUENCE communication.messages_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE communication.messages_id_seq OWNER TO user_ai;

--
-- Name: messages_id_seq; Type: SEQUENCE OWNED BY; Schema: communication; Owner: user_ai
--

ALTER SEQUENCE communication.messages_id_seq OWNED BY communication.messages.id;


--
-- Name: document_access_rules; Type: TABLE; Schema: data_feeds; Owner: user_ai
--

CREATE TABLE data_feeds.document_access_rules (
    id bigint NOT NULL,
    document_id integer NOT NULL,
    rule_type character varying(50) NOT NULL,
    match_expression character varying(512) NOT NULL,
    allow boolean DEFAULT true,
    metadata jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE data_feeds.document_access_rules OWNER TO user_ai;

--
-- Name: document_access_rules_id_seq; Type: SEQUENCE; Schema: data_feeds; Owner: user_ai
--

CREATE SEQUENCE data_feeds.document_access_rules_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE data_feeds.document_access_rules_id_seq OWNER TO user_ai;

--
-- Name: document_access_rules_id_seq; Type: SEQUENCE OWNED BY; Schema: data_feeds; Owner: user_ai
--

ALTER SEQUENCE data_feeds.document_access_rules_id_seq OWNED BY data_feeds.document_access_rules.id;


--
-- Name: document_deletion_log; Type: TABLE; Schema: data_feeds; Owner: user_ai
--

CREATE TABLE data_feeds.document_deletion_log (
    id integer NOT NULL,
    document_id integer,
    document_name text NOT NULL,
    deleted_by integer,
    deleted_at timestamp with time zone DEFAULT now(),
    reason text,
    vector_metadata_snapshot jsonb,
    file_type character varying(50),
    file_size_bytes bigint
);


ALTER TABLE data_feeds.document_deletion_log OWNER TO user_ai;

--
-- Name: TABLE document_deletion_log; Type: COMMENT; Schema: data_feeds; Owner: user_ai
--

COMMENT ON TABLE data_feeds.document_deletion_log IS 'Audit log of document deletions with metadata snapshots';


--
-- Name: document_deletion_log_id_seq; Type: SEQUENCE; Schema: data_feeds; Owner: user_ai
--

CREATE SEQUENCE data_feeds.document_deletion_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE data_feeds.document_deletion_log_id_seq OWNER TO user_ai;

--
-- Name: document_deletion_log_id_seq; Type: SEQUENCE OWNED BY; Schema: data_feeds; Owner: user_ai
--

ALTER SEQUENCE data_feeds.document_deletion_log_id_seq OWNED BY data_feeds.document_deletion_log.id;


--
-- Name: document_versions; Type: TABLE; Schema: data_feeds; Owner: user_ai
--

CREATE TABLE data_feeds.document_versions (
    id integer NOT NULL,
    document_id integer,
    version integer NOT NULL,
    embedding public.vector(384),
    content_snapshot text,
    metadata_snapshot jsonb,
    created_at timestamp with time zone DEFAULT now(),
    created_by integer
);


ALTER TABLE data_feeds.document_versions OWNER TO user_ai;

--
-- Name: TABLE document_versions; Type: COMMENT; Schema: data_feeds; Owner: user_ai
--

COMMENT ON TABLE data_feeds.document_versions IS 'Historical versions of documents for audit and recovery';


--
-- Name: document_versions_id_seq; Type: SEQUENCE; Schema: data_feeds; Owner: user_ai
--

CREATE SEQUENCE data_feeds.document_versions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE data_feeds.document_versions_id_seq OWNER TO user_ai;

--
-- Name: document_versions_id_seq; Type: SEQUENCE OWNED BY; Schema: data_feeds; Owner: user_ai
--

ALTER SEQUENCE data_feeds.document_versions_id_seq OWNED BY data_feeds.document_versions.id;


--
-- Name: documents; Type: TABLE; Schema: data_feeds; Owner: user_ai
--

CREATE TABLE data_feeds.documents (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    name text NOT NULL,
    description text,
    storage_uri text NOT NULL,
    storage_type text DEFAULT 'local'::text,
    classification text DEFAULT 'internal'::text,
    sensitivity_level text DEFAULT 'normal'::text,
    tags jsonb,
    allowed_recipients jsonb,
    allowed_contexts jsonb,
    blocked_contexts jsonb,
    shareable boolean DEFAULT false,
    allow_ai_to_suggest boolean DEFAULT false,
    max_share_count integer,
    share_count integer DEFAULT 0,
    retention_days integer DEFAULT 90,
    retention_expires_at timestamp with time zone,
    last_shared_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    file_size_bytes bigint,
    file_type character varying(50),
    original_content text,
    processed_content text,
    content_metadata jsonb DEFAULT '{}'::jsonb,
    embedding public.vector(384),
    vector_metadata jsonb DEFAULT '{}'::jsonb,
    ollama_model character varying(100),
    version integer DEFAULT 1,
    previous_embedding public.vector(384),
    last_modified_at timestamp with time zone,
    embedding_changed boolean DEFAULT false,
    is_deleted boolean DEFAULT false,
    deleted_at timestamp with time zone,
    deleted_by integer
);


ALTER TABLE data_feeds.documents OWNER TO user_ai;

--
-- Name: COLUMN documents.file_size_bytes; Type: COMMENT; Schema: data_feeds; Owner: user_ai
--

COMMENT ON COLUMN data_feeds.documents.file_size_bytes IS 'Size of uploaded file in bytes';


--
-- Name: COLUMN documents.file_type; Type: COMMENT; Schema: data_feeds; Owner: user_ai
--

COMMENT ON COLUMN data_feeds.documents.file_type IS 'Type of file: txt, csv, xlsx, or text_input';


--
-- Name: COLUMN documents.original_content; Type: COMMENT; Schema: data_feeds; Owner: user_ai
--

COMMENT ON COLUMN data_feeds.documents.original_content IS 'Raw content from uploaded file';


--
-- Name: COLUMN documents.processed_content; Type: COMMENT; Schema: data_feeds; Owner: user_ai
--

COMMENT ON COLUMN data_feeds.documents.processed_content IS 'Cleaned and parsed content ready for AI processing';


--
-- Name: COLUMN documents.content_metadata; Type: COMMENT; Schema: data_feeds; Owner: user_ai
--

COMMENT ON COLUMN data_feeds.documents.content_metadata IS 'Extraction metadata: row counts, columns, parsing info';


--
-- Name: COLUMN documents.embedding; Type: COMMENT; Schema: data_feeds; Owner: user_ai
--

COMMENT ON COLUMN data_feeds.documents.embedding IS 'OLLama-generated 384-dimensional embedding vector';


--
-- Name: COLUMN documents.vector_metadata; Type: COMMENT; Schema: data_feeds; Owner: user_ai
--

COMMENT ON COLUMN data_feeds.documents.vector_metadata IS 'Mapping of key concepts to table locations for semantic retrieval';


--
-- Name: COLUMN documents.ollama_model; Type: COMMENT; Schema: data_feeds; Owner: user_ai
--

COMMENT ON COLUMN data_feeds.documents.ollama_model IS 'Name/version of OLLama model used for processing';


--
-- Name: COLUMN documents.version; Type: COMMENT; Schema: data_feeds; Owner: user_ai
--

COMMENT ON COLUMN data_feeds.documents.version IS 'Version number of the document, incremented on content changes';


--
-- Name: COLUMN documents.previous_embedding; Type: COMMENT; Schema: data_feeds; Owner: user_ai
--

COMMENT ON COLUMN data_feeds.documents.previous_embedding IS 'Previous embedding vector for comparison';


--
-- Name: COLUMN documents.last_modified_at; Type: COMMENT; Schema: data_feeds; Owner: user_ai
--

COMMENT ON COLUMN data_feeds.documents.last_modified_at IS 'Timestamp of last content modification';


--
-- Name: COLUMN documents.embedding_changed; Type: COMMENT; Schema: data_feeds; Owner: user_ai
--

COMMENT ON COLUMN data_feeds.documents.embedding_changed IS 'Flag indicating if embedding changed in last update';


--
-- Name: COLUMN documents.is_deleted; Type: COMMENT; Schema: data_feeds; Owner: user_ai
--

COMMENT ON COLUMN data_feeds.documents.is_deleted IS 'Soft delete flag - if true, document is hidden from normal queries';


--
-- Name: COLUMN documents.deleted_at; Type: COMMENT; Schema: data_feeds; Owner: user_ai
--

COMMENT ON COLUMN data_feeds.documents.deleted_at IS 'Timestamp when document was soft deleted';


--
-- Name: COLUMN documents.deleted_by; Type: COMMENT; Schema: data_feeds; Owner: user_ai
--

COMMENT ON COLUMN data_feeds.documents.deleted_by IS 'User who deleted the document';


--
-- Name: documents_id_seq; Type: SEQUENCE; Schema: data_feeds; Owner: user_ai
--

CREATE SEQUENCE data_feeds.documents_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE data_feeds.documents_id_seq OWNER TO user_ai;

--
-- Name: documents_id_seq; Type: SEQUENCE OWNED BY; Schema: data_feeds; Owner: user_ai
--

ALTER SEQUENCE data_feeds.documents_id_seq OWNED BY data_feeds.documents.id;


--
-- Name: instruction_document_links; Type: TABLE; Schema: data_feeds; Owner: user_ai
--

CREATE TABLE data_feeds.instruction_document_links (
    id bigint NOT NULL,
    instruction_id integer NOT NULL,
    document_id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE data_feeds.instruction_document_links OWNER TO user_ai;

--
-- Name: instruction_document_links_id_seq; Type: SEQUENCE; Schema: data_feeds; Owner: user_ai
--

CREATE SEQUENCE data_feeds.instruction_document_links_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE data_feeds.instruction_document_links_id_seq OWNER TO user_ai;

--
-- Name: instruction_document_links_id_seq; Type: SEQUENCE OWNED BY; Schema: data_feeds; Owner: user_ai
--

ALTER SEQUENCE data_feeds.instruction_document_links_id_seq OWNED BY data_feeds.instruction_document_links.id;


--
-- Name: concepts; Type: TABLE; Schema: data_feeds_metadata; Owner: user_ai
--

CREATE TABLE data_feeds_metadata.concepts (
    id integer NOT NULL,
    file_id integer NOT NULL,
    concept_type character varying(50) NOT NULL,
    concept_value text NOT NULL,
    confidence_score double precision DEFAULT 1.0,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE data_feeds_metadata.concepts OWNER TO user_ai;

--
-- Name: TABLE concepts; Type: COMMENT; Schema: data_feeds_metadata; Owner: user_ai
--

COMMENT ON TABLE data_feeds_metadata.concepts IS 'Extracted concepts from documents (emails, names, etc.)';


--
-- Name: concepts_id_seq; Type: SEQUENCE; Schema: data_feeds_metadata; Owner: user_ai
--

CREATE SEQUENCE data_feeds_metadata.concepts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE data_feeds_metadata.concepts_id_seq OWNER TO user_ai;

--
-- Name: concepts_id_seq; Type: SEQUENCE OWNED BY; Schema: data_feeds_metadata; Owner: user_ai
--

ALTER SEQUENCE data_feeds_metadata.concepts_id_seq OWNED BY data_feeds_metadata.concepts.id;


--
-- Name: vector_mappings; Type: TABLE; Schema: data_feeds_metadata; Owner: user_ai
--

CREATE TABLE data_feeds_metadata.vector_mappings (
    id integer NOT NULL,
    vector_key character varying(100) NOT NULL,
    table_references text[] NOT NULL,
    file_id integer,
    metadata jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE data_feeds_metadata.vector_mappings OWNER TO user_ai;

--
-- Name: TABLE vector_mappings; Type: COMMENT; Schema: data_feeds_metadata; Owner: user_ai
--

COMMENT ON TABLE data_feeds_metadata.vector_mappings IS 'Mapping of vector keys to database table locations';


--
-- Name: vector_mappings_id_seq; Type: SEQUENCE; Schema: data_feeds_metadata; Owner: user_ai
--

CREATE SEQUENCE data_feeds_metadata.vector_mappings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE data_feeds_metadata.vector_mappings_id_seq OWNER TO user_ai;

--
-- Name: vector_mappings_id_seq; Type: SEQUENCE OWNED BY; Schema: data_feeds_metadata; Owner: user_ai
--

ALTER SEQUENCE data_feeds_metadata.vector_mappings_id_seq OWNED BY data_feeds_metadata.vector_mappings.id;


--
-- Name: embeddings; Type: TABLE; Schema: data_feeds_vectors; Owner: user_ai
--

CREATE TABLE data_feeds_vectors.embeddings (
    id integer NOT NULL,
    file_id integer NOT NULL,
    chunk_index integer DEFAULT 0,
    embedding public.vector(384) NOT NULL,
    content_snippet text,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE data_feeds_vectors.embeddings OWNER TO user_ai;

--
-- Name: TABLE embeddings; Type: COMMENT; Schema: data_feeds_vectors; Owner: user_ai
--

COMMENT ON TABLE data_feeds_vectors.embeddings IS 'Vector embeddings for document chunks';


--
-- Name: embeddings_id_seq; Type: SEQUENCE; Schema: data_feeds_vectors; Owner: user_ai
--

CREATE SEQUENCE data_feeds_vectors.embeddings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE data_feeds_vectors.embeddings_id_seq OWNER TO user_ai;

--
-- Name: embeddings_id_seq; Type: SEQUENCE OWNED BY; Schema: data_feeds_vectors; Owner: user_ai
--

ALTER SEQUENCE data_feeds_vectors.embeddings_id_seq OWNED BY data_feeds_vectors.embeddings.id;


--
-- Name: contact_group_members; Type: TABLE; Schema: user_management; Owner: user_ai
--

CREATE TABLE user_management.contact_group_members (
    id bigint NOT NULL,
    contact_id bigint NOT NULL,
    group_id bigint NOT NULL,
    added_at timestamp with time zone DEFAULT now()
);


ALTER TABLE user_management.contact_group_members OWNER TO user_ai;

--
-- Name: contact_group_members_id_seq; Type: SEQUENCE; Schema: user_management; Owner: user_ai
--

CREATE SEQUENCE user_management.contact_group_members_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE user_management.contact_group_members_id_seq OWNER TO user_ai;

--
-- Name: contact_group_members_id_seq; Type: SEQUENCE OWNED BY; Schema: user_management; Owner: user_ai
--

ALTER SEQUENCE user_management.contact_group_members_id_seq OWNED BY user_management.contact_group_members.id;


--
-- Name: contact_groups; Type: TABLE; Schema: user_management; Owner: user_ai
--

CREATE TABLE user_management.contact_groups (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    name text NOT NULL,
    description text,
    color_code text DEFAULT '#007bff'::text,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT contact_groups_color_format CHECK ((color_code ~ '^#[0-9A-Fa-f]{6}'::text))
);


ALTER TABLE user_management.contact_groups OWNER TO user_ai;

--
-- Name: contact_groups_id_seq; Type: SEQUENCE; Schema: user_management; Owner: user_ai
--

CREATE SEQUENCE user_management.contact_groups_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE user_management.contact_groups_id_seq OWNER TO user_ai;

--
-- Name: contact_groups_id_seq; Type: SEQUENCE OWNED BY; Schema: user_management; Owner: user_ai
--

ALTER SEQUENCE user_management.contact_groups_id_seq OWNED BY user_management.contact_groups.id;


--
-- Name: contacts; Type: TABLE; Schema: user_management; Owner: user_ai
--

CREATE TABLE user_management.contacts (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    phone_number text NOT NULL,
    display_name text,
    first_name text,
    last_name text,
    email text,
    avatar_url text,
    is_blocked boolean DEFAULT false,
    is_whitelisted boolean DEFAULT false,
    is_archived boolean DEFAULT false,
    trust_level integer DEFAULT 0,
    last_interaction_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT contacts_email_format CHECK (((email IS NULL) OR (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'::text))),
    CONSTRAINT contacts_phone_format CHECK ((phone_number ~ '^\+?[1-9]\d{1,14}'::text)),
    CONSTRAINT contacts_trust_level_check CHECK (((trust_level >= '-100'::integer) AND (trust_level <= 100)))
);


ALTER TABLE user_management.contacts OWNER TO user_ai;

--
-- Name: contacts_id_seq; Type: SEQUENCE; Schema: user_management; Owner: user_ai
--

CREATE SEQUENCE user_management.contacts_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE user_management.contacts_id_seq OWNER TO user_ai;

--
-- Name: contacts_id_seq; Type: SEQUENCE OWNED BY; Schema: user_management; Owner: user_ai
--

ALTER SEQUENCE user_management.contacts_id_seq OWNED BY user_management.contacts.id;


--
-- Name: user_settings; Type: TABLE; Schema: user_management; Owner: user_ai
--

CREATE TABLE user_management.user_settings (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    sms_forwarding_number text,
    call_forwarding_number text,
    ai_mode_enabled boolean DEFAULT true,
    ai_mode_expires_at timestamp with time zone,
    spam_filtering_enabled boolean DEFAULT true,
    recording_enabled boolean DEFAULT false,
    transcript_enabled boolean DEFAULT false,
    voice_cloning_enabled boolean DEFAULT false,
    timezone text DEFAULT 'UTC'::text,
    language_code text DEFAULT 'en'::text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT user_settings_language_valid CHECK ((language_code ~ '^[a-z]{2}(-[A-Z]{2})?'::text)),
    CONSTRAINT user_settings_timezone_valid CHECK ((timezone IS NOT NULL))
);


ALTER TABLE user_management.user_settings OWNER TO user_ai;

--
-- Name: user_settings_id_seq; Type: SEQUENCE; Schema: user_management; Owner: user_ai
--

CREATE SEQUENCE user_management.user_settings_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE user_management.user_settings_id_seq OWNER TO user_ai;

--
-- Name: user_settings_id_seq; Type: SEQUENCE OWNED BY; Schema: user_management; Owner: user_ai
--

ALTER SEQUENCE user_management.user_settings_id_seq OWNED BY user_management.user_settings.id;


--
-- Name: users; Type: TABLE; Schema: user_management; Owner: user_ai
--

CREATE TABLE user_management.users (
    id bigint NOT NULL,
    email text NOT NULL,
    password_hash text NOT NULL,
    phone_number text,
    is_active boolean DEFAULT true,
    email_verified boolean DEFAULT false,
    phone_verified boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    last_login_at timestamp with time zone,
    name text NOT NULL,
    password_reset_token text,
    password_reset_expires_at timestamp with time zone,
    email_verification_token text,
    phone_verification_token text,
    account_status text DEFAULT 'active'::text,
    failed_login_attempts integer DEFAULT 0,
    locked_until timestamp with time zone,
    last_activity_at timestamp with time zone,
    timezone text DEFAULT 'UTC'::text,
    language_code text DEFAULT 'en'::text,
    avatar_url text,
    bio text,
    privacy_level text DEFAULT 'standard'::text,
    email_notifications boolean DEFAULT true,
    sms_notifications boolean DEFAULT false,
    marketing_consent boolean DEFAULT false,
    data_processing_consent boolean DEFAULT false,
    consent_given_at timestamp with time zone,
    created_by text DEFAULT 'system'::text,
    updated_by text DEFAULT 'system'::text,
    deleted_at timestamp with time zone,
    version integer DEFAULT 1,
    CONSTRAINT users_account_status_check CHECK ((account_status = ANY (ARRAY['active'::text, 'suspended'::text, 'pending_verification'::text, 'deleted'::text]))),
    CONSTRAINT users_deleted_consistency CHECK ((((account_status = 'deleted'::text) AND (deleted_at IS NOT NULL)) OR ((account_status <> 'deleted'::text) AND (deleted_at IS NULL)))),
    CONSTRAINT users_email_format CHECK ((email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'::text)),
    CONSTRAINT users_language_valid CHECK ((language_code ~ '^[a-z]{2}(-[A-Z]{2})?'::text)),
    CONSTRAINT users_name_not_empty CHECK ((length(TRIM(BOTH FROM name)) > 0)),
    CONSTRAINT users_phone_format CHECK (((phone_number IS NULL) OR (phone_number ~ '^\+?[1-9]\d{1,14}'::text))),
    CONSTRAINT users_privacy_level_check CHECK ((privacy_level = ANY (ARRAY['minimal'::text, 'standard'::text, 'enhanced'::text, 'maximum'::text]))),
    CONSTRAINT users_timezone_valid CHECK ((timezone IS NOT NULL))
);


ALTER TABLE user_management.users OWNER TO user_ai;

--
-- Name: COLUMN users.name; Type: COMMENT; Schema: user_management; Owner: user_ai
--

COMMENT ON COLUMN user_management.users.name IS 'User display name';


--
-- Name: COLUMN users.password_reset_token; Type: COMMENT; Schema: user_management; Owner: user_ai
--

COMMENT ON COLUMN user_management.users.password_reset_token IS 'Token for password reset functionality';


--
-- Name: COLUMN users.password_reset_expires_at; Type: COMMENT; Schema: user_management; Owner: user_ai
--

COMMENT ON COLUMN user_management.users.password_reset_expires_at IS 'Expiration time for password reset token';


--
-- Name: COLUMN users.email_verification_token; Type: COMMENT; Schema: user_management; Owner: user_ai
--

COMMENT ON COLUMN user_management.users.email_verification_token IS 'Token for email verification';


--
-- Name: COLUMN users.phone_verification_token; Type: COMMENT; Schema: user_management; Owner: user_ai
--

COMMENT ON COLUMN user_management.users.phone_verification_token IS 'Token for phone verification';


--
-- Name: COLUMN users.account_status; Type: COMMENT; Schema: user_management; Owner: user_ai
--

COMMENT ON COLUMN user_management.users.account_status IS 'Current status of the user account';


--
-- Name: COLUMN users.failed_login_attempts; Type: COMMENT; Schema: user_management; Owner: user_ai
--

COMMENT ON COLUMN user_management.users.failed_login_attempts IS 'Number of consecutive failed login attempts';


--
-- Name: COLUMN users.locked_until; Type: COMMENT; Schema: user_management; Owner: user_ai
--

COMMENT ON COLUMN user_management.users.locked_until IS 'Account locked until this timestamp';


--
-- Name: COLUMN users.last_activity_at; Type: COMMENT; Schema: user_management; Owner: user_ai
--

COMMENT ON COLUMN user_management.users.last_activity_at IS 'Last time user was active';


--
-- Name: COLUMN users.timezone; Type: COMMENT; Schema: user_management; Owner: user_ai
--

COMMENT ON COLUMN user_management.users.timezone IS 'User preferred timezone';


--
-- Name: COLUMN users.language_code; Type: COMMENT; Schema: user_management; Owner: user_ai
--

COMMENT ON COLUMN user_management.users.language_code IS 'User preferred language code';


--
-- Name: COLUMN users.avatar_url; Type: COMMENT; Schema: user_management; Owner: user_ai
--

COMMENT ON COLUMN user_management.users.avatar_url IS 'URL to user avatar image';


--
-- Name: COLUMN users.bio; Type: COMMENT; Schema: user_management; Owner: user_ai
--

COMMENT ON COLUMN user_management.users.bio IS 'User biography/description';


--
-- Name: COLUMN users.privacy_level; Type: COMMENT; Schema: user_management; Owner: user_ai
--

COMMENT ON COLUMN user_management.users.privacy_level IS 'User privacy preference level';


--
-- Name: COLUMN users.email_notifications; Type: COMMENT; Schema: user_management; Owner: user_ai
--

COMMENT ON COLUMN user_management.users.email_notifications IS 'Whether user wants email notifications';


--
-- Name: COLUMN users.sms_notifications; Type: COMMENT; Schema: user_management; Owner: user_ai
--

COMMENT ON COLUMN user_management.users.sms_notifications IS 'Whether user wants SMS notifications';


--
-- Name: COLUMN users.marketing_consent; Type: COMMENT; Schema: user_management; Owner: user_ai
--

COMMENT ON COLUMN user_management.users.marketing_consent IS 'Whether user consented to marketing communications';


--
-- Name: COLUMN users.data_processing_consent; Type: COMMENT; Schema: user_management; Owner: user_ai
--

COMMENT ON COLUMN user_management.users.data_processing_consent IS 'Whether user consented to data processing';


--
-- Name: COLUMN users.consent_given_at; Type: COMMENT; Schema: user_management; Owner: user_ai
--

COMMENT ON COLUMN user_management.users.consent_given_at IS 'When consent was given';


--
-- Name: COLUMN users.created_by; Type: COMMENT; Schema: user_management; Owner: user_ai
--

COMMENT ON COLUMN user_management.users.created_by IS 'Who created this user record';


--
-- Name: COLUMN users.updated_by; Type: COMMENT; Schema: user_management; Owner: user_ai
--

COMMENT ON COLUMN user_management.users.updated_by IS 'Who last updated this user record';


--
-- Name: COLUMN users.deleted_at; Type: COMMENT; Schema: user_management; Owner: user_ai
--

COMMENT ON COLUMN user_management.users.deleted_at IS 'When user was soft deleted';


--
-- Name: COLUMN users.version; Type: COMMENT; Schema: user_management; Owner: user_ai
--

COMMENT ON COLUMN user_management.users.version IS 'Version number for optimistic locking';


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: user_management; Owner: user_ai
--

CREATE SEQUENCE user_management.users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE user_management.users_id_seq OWNER TO user_ai;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: user_management; Owner: user_ai
--

ALTER SEQUENCE user_management.users_id_seq OWNED BY user_management.users.id;


--
-- Name: ai_instructions id; Type: DEFAULT; Schema: ai_intelligence; Owner: user_ai
--

ALTER TABLE ONLY ai_intelligence.ai_instructions ALTER COLUMN id SET DEFAULT nextval('ai_intelligence.ai_instructions_id_seq'::regclass);


--
-- Name: embeddings id; Type: DEFAULT; Schema: ai_intelligence; Owner: user_ai
--

ALTER TABLE ONLY ai_intelligence.embeddings ALTER COLUMN id SET DEFAULT nextval('ai_intelligence.embeddings_id_seq'::regclass);


--
-- Name: feed_items id; Type: DEFAULT; Schema: ai_intelligence; Owner: user_ai
--

ALTER TABLE ONLY ai_intelligence.feed_items ALTER COLUMN id SET DEFAULT nextval('ai_intelligence.feed_items_id_seq'::regclass);


--
-- Name: ml_model_metrics id; Type: DEFAULT; Schema: ai_intelligence; Owner: user_ai
--

ALTER TABLE ONLY ai_intelligence.ml_model_metrics ALTER COLUMN id SET DEFAULT nextval('ai_intelligence.ml_model_metrics_id_seq'::regclass);


--
-- Name: policies id; Type: DEFAULT; Schema: ai_intelligence; Owner: user_ai
--

ALTER TABLE ONLY ai_intelligence.policies ALTER COLUMN id SET DEFAULT nextval('ai_intelligence.policies_id_seq'::regclass);


--
-- Name: spam_patterns id; Type: DEFAULT; Schema: ai_intelligence; Owner: user_ai
--

ALTER TABLE ONLY ai_intelligence.spam_patterns ALTER COLUMN id SET DEFAULT nextval('ai_intelligence.spam_patterns_id_seq'::regclass);


--
-- Name: voice_models id; Type: DEFAULT; Schema: ai_intelligence; Owner: user_ai
--

ALTER TABLE ONLY ai_intelligence.voice_models ALTER COLUMN id SET DEFAULT nextval('ai_intelligence.voice_models_id_seq'::regclass);


--
-- Name: ai_performance_metrics id; Type: DEFAULT; Schema: analytics; Owner: user_ai
--

ALTER TABLE ONLY analytics.ai_performance_metrics ALTER COLUMN id SET DEFAULT nextval('analytics.ai_performance_metrics_id_seq'::regclass);


--
-- Name: call_analytics id; Type: DEFAULT; Schema: analytics; Owner: user_ai
--

ALTER TABLE ONLY analytics.call_analytics ALTER COLUMN id SET DEFAULT nextval('analytics.call_analytics_id_seq'::regclass);


--
-- Name: contact_interaction_summary id; Type: DEFAULT; Schema: analytics; Owner: user_ai
--

ALTER TABLE ONLY analytics.contact_interaction_summary ALTER COLUMN id SET DEFAULT nextval('analytics.contact_interaction_summary_id_seq'::regclass);


--
-- Name: message_analytics id; Type: DEFAULT; Schema: analytics; Owner: user_ai
--

ALTER TABLE ONLY analytics.message_analytics ALTER COLUMN id SET DEFAULT nextval('analytics.message_analytics_id_seq'::regclass);


--
-- Name: monthly_reports id; Type: DEFAULT; Schema: analytics; Owner: user_ai
--

ALTER TABLE ONLY analytics.monthly_reports ALTER COLUMN id SET DEFAULT nextval('analytics.monthly_reports_id_seq'::regclass);


--
-- Name: system_performance_logs id; Type: DEFAULT; Schema: analytics; Owner: user_ai
--

ALTER TABLE ONLY analytics.system_performance_logs ALTER COLUMN id SET DEFAULT nextval('analytics.system_performance_logs_id_seq'::regclass);


--
-- Name: usage_statistics id; Type: DEFAULT; Schema: analytics; Owner: user_ai
--

ALTER TABLE ONLY analytics.usage_statistics ALTER COLUMN id SET DEFAULT nextval('analytics.usage_statistics_id_seq'::regclass);


--
-- Name: user_activity_logs id; Type: DEFAULT; Schema: analytics; Owner: user_ai
--

ALTER TABLE ONLY analytics.user_activity_logs ALTER COLUMN id SET DEFAULT nextval('analytics.user_activity_logs_id_seq'::regclass);


--
-- Name: weekly_reports id; Type: DEFAULT; Schema: analytics; Owner: user_ai
--

ALTER TABLE ONLY analytics.weekly_reports ALTER COLUMN id SET DEFAULT nextval('analytics.weekly_reports_id_seq'::regclass);


--
-- Name: calls id; Type: DEFAULT; Schema: communication; Owner: user_ai
--

ALTER TABLE ONLY communication.calls ALTER COLUMN id SET DEFAULT nextval('communication.calls_id_seq'::regclass);


--
-- Name: conversation_contexts id; Type: DEFAULT; Schema: communication; Owner: user_ai
--

ALTER TABLE ONLY communication.conversation_contexts ALTER COLUMN id SET DEFAULT nextval('communication.conversation_contexts_id_seq'::regclass);


--
-- Name: messages id; Type: DEFAULT; Schema: communication; Owner: user_ai
--

ALTER TABLE ONLY communication.messages ALTER COLUMN id SET DEFAULT nextval('communication.messages_id_seq'::regclass);


--
-- Name: document_access_rules id; Type: DEFAULT; Schema: data_feeds; Owner: user_ai
--

ALTER TABLE ONLY data_feeds.document_access_rules ALTER COLUMN id SET DEFAULT nextval('data_feeds.document_access_rules_id_seq'::regclass);


--
-- Name: document_deletion_log id; Type: DEFAULT; Schema: data_feeds; Owner: user_ai
--

ALTER TABLE ONLY data_feeds.document_deletion_log ALTER COLUMN id SET DEFAULT nextval('data_feeds.document_deletion_log_id_seq'::regclass);


--
-- Name: document_versions id; Type: DEFAULT; Schema: data_feeds; Owner: user_ai
--

ALTER TABLE ONLY data_feeds.document_versions ALTER COLUMN id SET DEFAULT nextval('data_feeds.document_versions_id_seq'::regclass);


--
-- Name: documents id; Type: DEFAULT; Schema: data_feeds; Owner: user_ai
--

ALTER TABLE ONLY data_feeds.documents ALTER COLUMN id SET DEFAULT nextval('data_feeds.documents_id_seq'::regclass);


--
-- Name: instruction_document_links id; Type: DEFAULT; Schema: data_feeds; Owner: user_ai
--

ALTER TABLE ONLY data_feeds.instruction_document_links ALTER COLUMN id SET DEFAULT nextval('data_feeds.instruction_document_links_id_seq'::regclass);


--
-- Name: concepts id; Type: DEFAULT; Schema: data_feeds_metadata; Owner: user_ai
--

ALTER TABLE ONLY data_feeds_metadata.concepts ALTER COLUMN id SET DEFAULT nextval('data_feeds_metadata.concepts_id_seq'::regclass);


--
-- Name: vector_mappings id; Type: DEFAULT; Schema: data_feeds_metadata; Owner: user_ai
--

ALTER TABLE ONLY data_feeds_metadata.vector_mappings ALTER COLUMN id SET DEFAULT nextval('data_feeds_metadata.vector_mappings_id_seq'::regclass);


--
-- Name: embeddings id; Type: DEFAULT; Schema: data_feeds_vectors; Owner: user_ai
--

ALTER TABLE ONLY data_feeds_vectors.embeddings ALTER COLUMN id SET DEFAULT nextval('data_feeds_vectors.embeddings_id_seq'::regclass);


--
-- Name: contact_group_members id; Type: DEFAULT; Schema: user_management; Owner: user_ai
--

ALTER TABLE ONLY user_management.contact_group_members ALTER COLUMN id SET DEFAULT nextval('user_management.contact_group_members_id_seq'::regclass);


--
-- Name: contact_groups id; Type: DEFAULT; Schema: user_management; Owner: user_ai
--

ALTER TABLE ONLY user_management.contact_groups ALTER COLUMN id SET DEFAULT nextval('user_management.contact_groups_id_seq'::regclass);


--
-- Name: contacts id; Type: DEFAULT; Schema: user_management; Owner: user_ai
--

ALTER TABLE ONLY user_management.contacts ALTER COLUMN id SET DEFAULT nextval('user_management.contacts_id_seq'::regclass);


--
-- Name: user_settings id; Type: DEFAULT; Schema: user_management; Owner: user_ai
--

ALTER TABLE ONLY user_management.user_settings ALTER COLUMN id SET DEFAULT nextval('user_management.user_settings_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: user_management; Owner: user_ai
--

ALTER TABLE ONLY user_management.users ALTER COLUMN id SET DEFAULT nextval('user_management.users_id_seq'::regclass);


--
-- Data for Name: ai_instructions; Type: TABLE DATA; Schema: ai_intelligence; Owner: user_ai
--

COPY ai_intelligence.ai_instructions (id, user_id, title, instruction_text, instruction_type, context_type, channel, target_identifier, context_tags, priority, priority_weight, status, verification_required, verification_method, verification_data, usage_count, max_usage, last_triggered_at, expires_at, auto_archive_at, completed_at, archived_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: embeddings; Type: TABLE DATA; Schema: ai_intelligence; Owner: user_ai
--

COPY ai_intelligence.embeddings (id, user_id, content_type, content_id, content_text, embedding, model_name, model_version, created_at) FROM stdin;
\.


--
-- Data for Name: feed_items; Type: TABLE DATA; Schema: ai_intelligence; Owner: user_ai
--

COPY ai_intelligence.feed_items (id, user_id, title, body, tags, priority, status, is_sensitive, embedding, created_at, updated_at, expires_at, last_accessed_at) FROM stdin;
\.


--
-- Data for Name: labs_images; Type: TABLE DATA; Schema: ai_intelligence; Owner: user_ai
--

COPY ai_intelligence.labs_images (image_id, convo_id, user_id, url, caption, embedding, created_at) FROM stdin;
\.


--
-- Data for Name: labs_message_chunks; Type: TABLE DATA; Schema: ai_intelligence; Owner: user_ai
--

COPY ai_intelligence.labs_message_chunks (chunk_id, message_id, ord, text, embedding) FROM stdin;
\.


--
-- Data for Name: labs_messages; Type: TABLE DATA; Schema: ai_intelligence; Owner: user_ai
--

COPY ai_intelligence.labs_messages (message_id, convo_id, user_id, source_lang, target_lang, raw_text, final_summary, created_at) FROM stdin;
\.


--
-- Data for Name: ml_model_metrics; Type: TABLE DATA; Schema: ai_intelligence; Owner: user_ai
--

COPY ai_intelligence.ml_model_metrics (id, model_name, model_version, metric_type, metric_value, dataset_size, evaluation_date, metadata) FROM stdin;
\.


--
-- Data for Name: policies; Type: TABLE DATA; Schema: ai_intelligence; Owner: user_ai
--

COPY ai_intelligence.policies (id, user_id, title, body_text, policy_type, tags, is_active, priority, embedding, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: spam_patterns; Type: TABLE DATA; Schema: ai_intelligence; Owner: user_ai
--

COPY ai_intelligence.spam_patterns (id, pattern_type, pattern_value, confidence_score, is_active, source, created_by, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: voice_models; Type: TABLE DATA; Schema: ai_intelligence; Owner: user_ai
--

COPY ai_intelligence.voice_models (id, user_id, model_name, voice_sample_uri, model_uri, training_status, quality_score, is_active, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: ai_performance_metrics; Type: TABLE DATA; Schema: analytics; Owner: user_ai
--

COPY analytics.ai_performance_metrics (id, user_id, metric_date, metric_type, metric_value, sample_size, model_version, context_data, created_at) FROM stdin;
\.


--
-- Data for Name: call_analytics; Type: TABLE DATA; Schema: analytics; Owner: user_ai
--

COPY analytics.call_analytics (id, user_id, call_id, analysis_type, analysis_result, confidence_score, model_used, processing_time_ms, tokens_processed, cost_estimate, created_at) FROM stdin;
\.


--
-- Data for Name: contact_interaction_summary; Type: TABLE DATA; Schema: analytics; Owner: user_ai
--

COPY analytics.contact_interaction_summary (id, user_id, contact_id, summary_date, total_calls, total_messages, total_call_duration_seconds, last_interaction_type, last_interaction_at, interaction_frequency_score, relationship_strength, avg_sentiment_score, spam_likelihood, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: message_analytics; Type: TABLE DATA; Schema: analytics; Owner: user_ai
--

COPY analytics.message_analytics (id, user_id, message_id, analysis_type, analysis_result, confidence_score, model_used, processing_time_ms, tokens_processed, cost_estimate, created_at) FROM stdin;
\.


--
-- Data for Name: monthly_reports; Type: TABLE DATA; Schema: analytics; Owner: user_ai
--

COPY analytics.monthly_reports (id, user_id, report_month, start_date, end_date, total_calls, total_messages, total_call_duration_seconds, spam_calls_blocked, spam_messages_blocked, ai_interactions, most_contacted_numbers, call_patterns, message_patterns, ai_effectiveness_score, cost_savings_estimate, created_at) FROM stdin;
\.


--
-- Data for Name: system_performance_logs; Type: TABLE DATA; Schema: analytics; Owner: user_ai
--

COPY analytics.system_performance_logs (id, log_timestamp, component_name, metric_type, metric_value, unit, server_instance, additional_data) FROM stdin;
\.


--
-- Data for Name: usage_statistics; Type: TABLE DATA; Schema: analytics; Owner: user_ai
--

COPY analytics.usage_statistics (id, user_id, stat_date, calls_handled_by_ai, messages_processed, spam_blocked, ai_instructions_used, voice_cloning_minutes, transcription_minutes, api_calls_made, storage_used_mb, bandwidth_used_mb, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: user_activity_logs; Type: TABLE DATA; Schema: analytics; Owner: user_ai
--

COPY analytics.user_activity_logs (id, user_id, activity_type, activity_details, ip_address, user_agent, session_id, duration_seconds, success, error_message, created_at) FROM stdin;
\.


--
-- Data for Name: weekly_reports; Type: TABLE DATA; Schema: analytics; Owner: user_ai
--

COPY analytics.weekly_reports (id, user_id, report_week, start_date, end_date, total_calls, total_messages, total_call_duration_seconds, spam_calls_blocked, spam_messages_blocked, ai_interactions, peak_call_hours, top_contacts, sentiment_summary, average_call_duration, busiest_day_of_week, total_ai_responses, emergency_calls, created_at) FROM stdin;
\.


--
-- Data for Name: calls; Type: TABLE DATA; Schema: communication; Owner: user_ai
--

COPY communication.calls (id, user_id, contact_id, from_number, to_number, direction, status, started_at, answered_at, ended_at, duration_seconds, intent, urgency, outcome, transcript, transcript_confidence, recording_uri, recording_duration_seconds, spam_score, is_spam, ai_handled, policy_ids, metadata, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: conversation_contexts; Type: TABLE DATA; Schema: communication; Owner: user_ai
--

COPY communication.conversation_contexts (id, user_id, conversation_id, context_type, summary, key_topics, sentiment_analysis, participant_count, start_time, end_time, is_active, metadata, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: messages; Type: TABLE DATA; Schema: communication; Owner: user_ai
--

COPY communication.messages (id, user_id, contact_id, conversation_id, phone_number, direction, message_body, message_type, status, is_spam, spam_score, is_read, intent, sentiment, ai_response, media_urls, metadata, sent_at, received_at, read_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: document_access_rules; Type: TABLE DATA; Schema: data_feeds; Owner: user_ai
--

COPY data_feeds.document_access_rules (id, document_id, rule_type, match_expression, allow, metadata, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: document_deletion_log; Type: TABLE DATA; Schema: data_feeds; Owner: user_ai
--

COPY data_feeds.document_deletion_log (id, document_id, document_name, deleted_by, deleted_at, reason, vector_metadata_snapshot, file_type, file_size_bytes) FROM stdin;
\.


--
-- Data for Name: document_versions; Type: TABLE DATA; Schema: data_feeds; Owner: user_ai
--

COPY data_feeds.document_versions (id, document_id, version, embedding, content_snapshot, metadata_snapshot, created_at, created_by) FROM stdin;
\.


--
-- Data for Name: documents; Type: TABLE DATA; Schema: data_feeds; Owner: user_ai
--

COPY data_feeds.documents (id, user_id, name, description, storage_uri, storage_type, classification, sensitivity_level, tags, allowed_recipients, allowed_contexts, blocked_contexts, shareable, allow_ai_to_suggest, max_share_count, share_count, retention_days, retention_expires_at, last_shared_at, created_at, updated_at, file_size_bytes, file_type, original_content, processed_content, content_metadata, embedding, vector_metadata, ollama_model, version, previous_embedding, last_modified_at, embedding_changed, is_deleted, deleted_at, deleted_by) FROM stdin;
\.


--
-- Data for Name: instruction_document_links; Type: TABLE DATA; Schema: data_feeds; Owner: user_ai
--

COPY data_feeds.instruction_document_links (id, instruction_id, document_id, created_at) FROM stdin;
\.


--
-- Data for Name: concepts; Type: TABLE DATA; Schema: data_feeds_metadata; Owner: user_ai
--

COPY data_feeds_metadata.concepts (id, file_id, concept_type, concept_value, confidence_score, is_active, created_at) FROM stdin;
\.


--
-- Data for Name: vector_mappings; Type: TABLE DATA; Schema: data_feeds_metadata; Owner: user_ai
--

COPY data_feeds_metadata.vector_mappings (id, vector_key, table_references, file_id, metadata, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: embeddings; Type: TABLE DATA; Schema: data_feeds_vectors; Owner: user_ai
--

COPY data_feeds_vectors.embeddings (id, file_id, chunk_index, embedding, content_snippet, is_active, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: contact_group_members; Type: TABLE DATA; Schema: user_management; Owner: user_ai
--

COPY user_management.contact_group_members (id, contact_id, group_id, added_at) FROM stdin;
\.


--
-- Data for Name: contact_groups; Type: TABLE DATA; Schema: user_management; Owner: user_ai
--

COPY user_management.contact_groups (id, user_id, name, description, color_code, created_at) FROM stdin;
\.


--
-- Data for Name: contacts; Type: TABLE DATA; Schema: user_management; Owner: user_ai
--

COPY user_management.contacts (id, user_id, phone_number, display_name, first_name, last_name, email, avatar_url, is_blocked, is_whitelisted, is_archived, trust_level, last_interaction_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: user_settings; Type: TABLE DATA; Schema: user_management; Owner: user_ai
--

COPY user_management.user_settings (id, user_id, sms_forwarding_number, call_forwarding_number, ai_mode_enabled, ai_mode_expires_at, spam_filtering_enabled, recording_enabled, transcript_enabled, voice_cloning_enabled, timezone, language_code, created_at, updated_at) FROM stdin;
1	3	\N	\N	t	\N	t	f	f	f	UTC	en	2025-09-23 22:30:44.239827+00	2025-09-23 22:30:44.239827+00
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: user_management; Owner: user_ai
--

COPY user_management.users (id, email, password_hash, phone_number, is_active, email_verified, phone_verified, created_at, updated_at, last_login_at, name, password_reset_token, password_reset_expires_at, email_verification_token, phone_verification_token, account_status, failed_login_attempts, locked_until, last_activity_at, timezone, language_code, avatar_url, bio, privacy_level, email_notifications, sms_notifications, marketing_consent, data_processing_consent, consent_given_at, created_by, updated_by, deleted_at, version) FROM stdin;
3	test@quell-ai.com	a1b2c3d4e5f6789012345678901234567890123456789012345678901234:8f4e5c2b1a9d8e7f6c3b2a1e9d8c7b6a5f4e3d2c1b0a9e8d7c6b5a4f3e2d1c0b9a8e7f6c5b4a3e2d1c0b9a8e7f6c5b4a3e2d1c0	+15551234567	t	f	f	2025-09-23 22:30:44.239827+00	2025-09-23 22:30:44.239827+00	\N	Test User	\N	\N	\N	\N	active	0	\N	\N	UTC	en	\N	\N	standard	t	f	f	t	2025-09-23 22:30:44.239827+00	system	system	\N	1
\.


--
-- Name: ai_instructions_id_seq; Type: SEQUENCE SET; Schema: ai_intelligence; Owner: user_ai
--

SELECT pg_catalog.setval('ai_intelligence.ai_instructions_id_seq', 1, false);


--
-- Name: embeddings_id_seq; Type: SEQUENCE SET; Schema: ai_intelligence; Owner: user_ai
--

SELECT pg_catalog.setval('ai_intelligence.embeddings_id_seq', 1, false);


--
-- Name: feed_items_id_seq; Type: SEQUENCE SET; Schema: ai_intelligence; Owner: user_ai
--

SELECT pg_catalog.setval('ai_intelligence.feed_items_id_seq', 1, false);


--
-- Name: ml_model_metrics_id_seq; Type: SEQUENCE SET; Schema: ai_intelligence; Owner: user_ai
--

SELECT pg_catalog.setval('ai_intelligence.ml_model_metrics_id_seq', 1, false);


--
-- Name: policies_id_seq; Type: SEQUENCE SET; Schema: ai_intelligence; Owner: user_ai
--

SELECT pg_catalog.setval('ai_intelligence.policies_id_seq', 1, false);


--
-- Name: spam_patterns_id_seq; Type: SEQUENCE SET; Schema: ai_intelligence; Owner: user_ai
--

SELECT pg_catalog.setval('ai_intelligence.spam_patterns_id_seq', 1, false);


--
-- Name: voice_models_id_seq; Type: SEQUENCE SET; Schema: ai_intelligence; Owner: user_ai
--

SELECT pg_catalog.setval('ai_intelligence.voice_models_id_seq', 1, false);


--
-- Name: ai_performance_metrics_id_seq; Type: SEQUENCE SET; Schema: analytics; Owner: user_ai
--

SELECT pg_catalog.setval('analytics.ai_performance_metrics_id_seq', 1, false);


--
-- Name: call_analytics_id_seq; Type: SEQUENCE SET; Schema: analytics; Owner: user_ai
--

SELECT pg_catalog.setval('analytics.call_analytics_id_seq', 1, false);


--
-- Name: contact_interaction_summary_id_seq; Type: SEQUENCE SET; Schema: analytics; Owner: user_ai
--

SELECT pg_catalog.setval('analytics.contact_interaction_summary_id_seq', 1, false);


--
-- Name: message_analytics_id_seq; Type: SEQUENCE SET; Schema: analytics; Owner: user_ai
--

SELECT pg_catalog.setval('analytics.message_analytics_id_seq', 1, false);


--
-- Name: monthly_reports_id_seq; Type: SEQUENCE SET; Schema: analytics; Owner: user_ai
--

SELECT pg_catalog.setval('analytics.monthly_reports_id_seq', 1, false);


--
-- Name: system_performance_logs_id_seq; Type: SEQUENCE SET; Schema: analytics; Owner: user_ai
--

SELECT pg_catalog.setval('analytics.system_performance_logs_id_seq', 1, false);


--
-- Name: usage_statistics_id_seq; Type: SEQUENCE SET; Schema: analytics; Owner: user_ai
--

SELECT pg_catalog.setval('analytics.usage_statistics_id_seq', 1, false);


--
-- Name: user_activity_logs_id_seq; Type: SEQUENCE SET; Schema: analytics; Owner: user_ai
--

SELECT pg_catalog.setval('analytics.user_activity_logs_id_seq', 1, false);


--
-- Name: weekly_reports_id_seq; Type: SEQUENCE SET; Schema: analytics; Owner: user_ai
--

SELECT pg_catalog.setval('analytics.weekly_reports_id_seq', 1, false);


--
-- Name: calls_id_seq; Type: SEQUENCE SET; Schema: communication; Owner: user_ai
--

SELECT pg_catalog.setval('communication.calls_id_seq', 1, false);


--
-- Name: conversation_contexts_id_seq; Type: SEQUENCE SET; Schema: communication; Owner: user_ai
--

SELECT pg_catalog.setval('communication.conversation_contexts_id_seq', 1, false);


--
-- Name: messages_id_seq; Type: SEQUENCE SET; Schema: communication; Owner: user_ai
--

SELECT pg_catalog.setval('communication.messages_id_seq', 1, false);


--
-- Name: document_access_rules_id_seq; Type: SEQUENCE SET; Schema: data_feeds; Owner: user_ai
--

SELECT pg_catalog.setval('data_feeds.document_access_rules_id_seq', 1, false);


--
-- Name: document_deletion_log_id_seq; Type: SEQUENCE SET; Schema: data_feeds; Owner: user_ai
--

SELECT pg_catalog.setval('data_feeds.document_deletion_log_id_seq', 1, false);


--
-- Name: document_versions_id_seq; Type: SEQUENCE SET; Schema: data_feeds; Owner: user_ai
--

SELECT pg_catalog.setval('data_feeds.document_versions_id_seq', 1, false);


--
-- Name: documents_id_seq; Type: SEQUENCE SET; Schema: data_feeds; Owner: user_ai
--

SELECT pg_catalog.setval('data_feeds.documents_id_seq', 1, false);


--
-- Name: instruction_document_links_id_seq; Type: SEQUENCE SET; Schema: data_feeds; Owner: user_ai
--

SELECT pg_catalog.setval('data_feeds.instruction_document_links_id_seq', 1, false);


--
-- Name: concepts_id_seq; Type: SEQUENCE SET; Schema: data_feeds_metadata; Owner: user_ai
--

SELECT pg_catalog.setval('data_feeds_metadata.concepts_id_seq', 1, false);


--
-- Name: vector_mappings_id_seq; Type: SEQUENCE SET; Schema: data_feeds_metadata; Owner: user_ai
--

SELECT pg_catalog.setval('data_feeds_metadata.vector_mappings_id_seq', 1, false);


--
-- Name: embeddings_id_seq; Type: SEQUENCE SET; Schema: data_feeds_vectors; Owner: user_ai
--

SELECT pg_catalog.setval('data_feeds_vectors.embeddings_id_seq', 1, false);


--
-- Name: contact_group_members_id_seq; Type: SEQUENCE SET; Schema: user_management; Owner: user_ai
--

SELECT pg_catalog.setval('user_management.contact_group_members_id_seq', 1, false);


--
-- Name: contact_groups_id_seq; Type: SEQUENCE SET; Schema: user_management; Owner: user_ai
--

SELECT pg_catalog.setval('user_management.contact_groups_id_seq', 1, false);


--
-- Name: contacts_id_seq; Type: SEQUENCE SET; Schema: user_management; Owner: user_ai
--

SELECT pg_catalog.setval('user_management.contacts_id_seq', 1, false);


--
-- Name: user_settings_id_seq; Type: SEQUENCE SET; Schema: user_management; Owner: user_ai
--

SELECT pg_catalog.setval('user_management.user_settings_id_seq', 1, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: user_management; Owner: user_ai
--

SELECT pg_catalog.setval('user_management.users_id_seq', 4, true);


--
-- Name: ai_instructions ai_instructions_pkey; Type: CONSTRAINT; Schema: ai_intelligence; Owner: user_ai
--

ALTER TABLE ONLY ai_intelligence.ai_instructions
    ADD CONSTRAINT ai_instructions_pkey PRIMARY KEY (id);


--
-- Name: embeddings embeddings_pkey; Type: CONSTRAINT; Schema: ai_intelligence; Owner: user_ai
--

ALTER TABLE ONLY ai_intelligence.embeddings
    ADD CONSTRAINT embeddings_pkey PRIMARY KEY (id);


--
-- Name: embeddings embeddings_user_content_unique; Type: CONSTRAINT; Schema: ai_intelligence; Owner: user_ai
--

ALTER TABLE ONLY ai_intelligence.embeddings
    ADD CONSTRAINT embeddings_user_content_unique UNIQUE (user_id, content_type, content_id);


--
-- Name: feed_items feed_items_pkey; Type: CONSTRAINT; Schema: ai_intelligence; Owner: user_ai
--

ALTER TABLE ONLY ai_intelligence.feed_items
    ADD CONSTRAINT feed_items_pkey PRIMARY KEY (id);


--
-- Name: labs_images labs_images_pkey; Type: CONSTRAINT; Schema: ai_intelligence; Owner: user_ai
--

ALTER TABLE ONLY ai_intelligence.labs_images
    ADD CONSTRAINT labs_images_pkey PRIMARY KEY (image_id);


--
-- Name: labs_message_chunks labs_message_chunks_pkey; Type: CONSTRAINT; Schema: ai_intelligence; Owner: user_ai
--

ALTER TABLE ONLY ai_intelligence.labs_message_chunks
    ADD CONSTRAINT labs_message_chunks_pkey PRIMARY KEY (chunk_id);


--
-- Name: labs_messages labs_messages_pkey; Type: CONSTRAINT; Schema: ai_intelligence; Owner: user_ai
--

ALTER TABLE ONLY ai_intelligence.labs_messages
    ADD CONSTRAINT labs_messages_pkey PRIMARY KEY (message_id);


--
-- Name: ml_model_metrics ml_metrics_model_version_metric_unique; Type: CONSTRAINT; Schema: ai_intelligence; Owner: user_ai
--

ALTER TABLE ONLY ai_intelligence.ml_model_metrics
    ADD CONSTRAINT ml_metrics_model_version_metric_unique UNIQUE (model_name, model_version, metric_type);


--
-- Name: ml_model_metrics ml_model_metrics_pkey; Type: CONSTRAINT; Schema: ai_intelligence; Owner: user_ai
--

ALTER TABLE ONLY ai_intelligence.ml_model_metrics
    ADD CONSTRAINT ml_model_metrics_pkey PRIMARY KEY (id);


--
-- Name: policies policies_pkey; Type: CONSTRAINT; Schema: ai_intelligence; Owner: user_ai
--

ALTER TABLE ONLY ai_intelligence.policies
    ADD CONSTRAINT policies_pkey PRIMARY KEY (id);


--
-- Name: spam_patterns spam_patterns_pkey; Type: CONSTRAINT; Schema: ai_intelligence; Owner: user_ai
--

ALTER TABLE ONLY ai_intelligence.spam_patterns
    ADD CONSTRAINT spam_patterns_pkey PRIMARY KEY (id);


--
-- Name: voice_models voice_models_pkey; Type: CONSTRAINT; Schema: ai_intelligence; Owner: user_ai
--

ALTER TABLE ONLY ai_intelligence.voice_models
    ADD CONSTRAINT voice_models_pkey PRIMARY KEY (id);


--
-- Name: voice_models voice_models_user_name_unique; Type: CONSTRAINT; Schema: ai_intelligence; Owner: user_ai
--

ALTER TABLE ONLY ai_intelligence.voice_models
    ADD CONSTRAINT voice_models_user_name_unique UNIQUE (user_id, model_name);


--
-- Name: ai_performance_metrics ai_performance_metrics_pkey; Type: CONSTRAINT; Schema: analytics; Owner: user_ai
--

ALTER TABLE ONLY analytics.ai_performance_metrics
    ADD CONSTRAINT ai_performance_metrics_pkey PRIMARY KEY (id);


--
-- Name: ai_performance_metrics ai_performance_metrics_unique; Type: CONSTRAINT; Schema: analytics; Owner: user_ai
--

ALTER TABLE ONLY analytics.ai_performance_metrics
    ADD CONSTRAINT ai_performance_metrics_unique UNIQUE (user_id, metric_date, metric_type, model_version);


--
-- Name: call_analytics call_analytics_call_type_unique; Type: CONSTRAINT; Schema: analytics; Owner: user_ai
--

ALTER TABLE ONLY analytics.call_analytics
    ADD CONSTRAINT call_analytics_call_type_unique UNIQUE (call_id, analysis_type);


--
-- Name: call_analytics call_analytics_pkey; Type: CONSTRAINT; Schema: analytics; Owner: user_ai
--

ALTER TABLE ONLY analytics.call_analytics
    ADD CONSTRAINT call_analytics_pkey PRIMARY KEY (id);


--
-- Name: contact_interaction_summary contact_interaction_summary_pkey; Type: CONSTRAINT; Schema: analytics; Owner: user_ai
--

ALTER TABLE ONLY analytics.contact_interaction_summary
    ADD CONSTRAINT contact_interaction_summary_pkey PRIMARY KEY (id);


--
-- Name: contact_interaction_summary contact_interaction_summary_unique; Type: CONSTRAINT; Schema: analytics; Owner: user_ai
--

ALTER TABLE ONLY analytics.contact_interaction_summary
    ADD CONSTRAINT contact_interaction_summary_unique UNIQUE (user_id, contact_id, summary_date);


--
-- Name: message_analytics message_analytics_message_type_unique; Type: CONSTRAINT; Schema: analytics; Owner: user_ai
--

ALTER TABLE ONLY analytics.message_analytics
    ADD CONSTRAINT message_analytics_message_type_unique UNIQUE (message_id, analysis_type);


--
-- Name: message_analytics message_analytics_pkey; Type: CONSTRAINT; Schema: analytics; Owner: user_ai
--

ALTER TABLE ONLY analytics.message_analytics
    ADD CONSTRAINT message_analytics_pkey PRIMARY KEY (id);


--
-- Name: monthly_reports monthly_reports_pkey; Type: CONSTRAINT; Schema: analytics; Owner: user_ai
--

ALTER TABLE ONLY analytics.monthly_reports
    ADD CONSTRAINT monthly_reports_pkey PRIMARY KEY (id);


--
-- Name: monthly_reports monthly_reports_user_month_unique; Type: CONSTRAINT; Schema: analytics; Owner: user_ai
--

ALTER TABLE ONLY analytics.monthly_reports
    ADD CONSTRAINT monthly_reports_user_month_unique UNIQUE (user_id, report_month);


--
-- Name: system_performance_logs system_performance_logs_pkey; Type: CONSTRAINT; Schema: analytics; Owner: user_ai
--

ALTER TABLE ONLY analytics.system_performance_logs
    ADD CONSTRAINT system_performance_logs_pkey PRIMARY KEY (id);


--
-- Name: system_performance_logs system_performance_logs_timestamp_component; Type: CONSTRAINT; Schema: analytics; Owner: user_ai
--

ALTER TABLE ONLY analytics.system_performance_logs
    ADD CONSTRAINT system_performance_logs_timestamp_component UNIQUE (log_timestamp, component_name, metric_type);


--
-- Name: usage_statistics usage_statistics_pkey; Type: CONSTRAINT; Schema: analytics; Owner: user_ai
--

ALTER TABLE ONLY analytics.usage_statistics
    ADD CONSTRAINT usage_statistics_pkey PRIMARY KEY (id);


--
-- Name: usage_statistics usage_statistics_user_date_unique; Type: CONSTRAINT; Schema: analytics; Owner: user_ai
--

ALTER TABLE ONLY analytics.usage_statistics
    ADD CONSTRAINT usage_statistics_user_date_unique UNIQUE (user_id, stat_date);


--
-- Name: user_activity_logs user_activity_logs_pkey; Type: CONSTRAINT; Schema: analytics; Owner: user_ai
--

ALTER TABLE ONLY analytics.user_activity_logs
    ADD CONSTRAINT user_activity_logs_pkey PRIMARY KEY (id);


--
-- Name: weekly_reports weekly_reports_pkey; Type: CONSTRAINT; Schema: analytics; Owner: user_ai
--

ALTER TABLE ONLY analytics.weekly_reports
    ADD CONSTRAINT weekly_reports_pkey PRIMARY KEY (id);


--
-- Name: weekly_reports weekly_reports_user_week_unique; Type: CONSTRAINT; Schema: analytics; Owner: user_ai
--

ALTER TABLE ONLY analytics.weekly_reports
    ADD CONSTRAINT weekly_reports_user_week_unique UNIQUE (user_id, report_week);


--
-- Name: calls calls_pkey; Type: CONSTRAINT; Schema: communication; Owner: user_ai
--

ALTER TABLE ONLY communication.calls
    ADD CONSTRAINT calls_pkey PRIMARY KEY (id);


--
-- Name: conversation_contexts conversation_contexts_pkey; Type: CONSTRAINT; Schema: communication; Owner: user_ai
--

ALTER TABLE ONLY communication.conversation_contexts
    ADD CONSTRAINT conversation_contexts_pkey PRIMARY KEY (id);


--
-- Name: conversation_contexts conversation_contexts_user_conv_unique; Type: CONSTRAINT; Schema: communication; Owner: user_ai
--

ALTER TABLE ONLY communication.conversation_contexts
    ADD CONSTRAINT conversation_contexts_user_conv_unique UNIQUE (user_id, conversation_id);


--
-- Name: messages messages_pkey; Type: CONSTRAINT; Schema: communication; Owner: user_ai
--

ALTER TABLE ONLY communication.messages
    ADD CONSTRAINT messages_pkey PRIMARY KEY (id);


--
-- Name: document_access_rules document_access_rules_pkey; Type: CONSTRAINT; Schema: data_feeds; Owner: user_ai
--

ALTER TABLE ONLY data_feeds.document_access_rules
    ADD CONSTRAINT document_access_rules_pkey PRIMARY KEY (id);


--
-- Name: document_deletion_log document_deletion_log_pkey; Type: CONSTRAINT; Schema: data_feeds; Owner: user_ai
--

ALTER TABLE ONLY data_feeds.document_deletion_log
    ADD CONSTRAINT document_deletion_log_pkey PRIMARY KEY (id);


--
-- Name: document_versions document_versions_pkey; Type: CONSTRAINT; Schema: data_feeds; Owner: user_ai
--

ALTER TABLE ONLY data_feeds.document_versions
    ADD CONSTRAINT document_versions_pkey PRIMARY KEY (id);


--
-- Name: documents documents_pkey; Type: CONSTRAINT; Schema: data_feeds; Owner: user_ai
--

ALTER TABLE ONLY data_feeds.documents
    ADD CONSTRAINT documents_pkey PRIMARY KEY (id);


--
-- Name: instruction_document_links instruction_document_links_pkey; Type: CONSTRAINT; Schema: data_feeds; Owner: user_ai
--

ALTER TABLE ONLY data_feeds.instruction_document_links
    ADD CONSTRAINT instruction_document_links_pkey PRIMARY KEY (id);


--
-- Name: concepts concepts_pkey; Type: CONSTRAINT; Schema: data_feeds_metadata; Owner: user_ai
--

ALTER TABLE ONLY data_feeds_metadata.concepts
    ADD CONSTRAINT concepts_pkey PRIMARY KEY (id);


--
-- Name: vector_mappings vector_mappings_pkey; Type: CONSTRAINT; Schema: data_feeds_metadata; Owner: user_ai
--

ALTER TABLE ONLY data_feeds_metadata.vector_mappings
    ADD CONSTRAINT vector_mappings_pkey PRIMARY KEY (id);


--
-- Name: vector_mappings vector_mappings_vector_key_key; Type: CONSTRAINT; Schema: data_feeds_metadata; Owner: user_ai
--

ALTER TABLE ONLY data_feeds_metadata.vector_mappings
    ADD CONSTRAINT vector_mappings_vector_key_key UNIQUE (vector_key);


--
-- Name: embeddings embeddings_pkey; Type: CONSTRAINT; Schema: data_feeds_vectors; Owner: user_ai
--

ALTER TABLE ONLY data_feeds_vectors.embeddings
    ADD CONSTRAINT embeddings_pkey PRIMARY KEY (id);


--
-- Name: contact_group_members contact_group_members_pkey; Type: CONSTRAINT; Schema: user_management; Owner: user_ai
--

ALTER TABLE ONLY user_management.contact_group_members
    ADD CONSTRAINT contact_group_members_pkey PRIMARY KEY (id);


--
-- Name: contact_group_members contact_group_members_unique; Type: CONSTRAINT; Schema: user_management; Owner: user_ai
--

ALTER TABLE ONLY user_management.contact_group_members
    ADD CONSTRAINT contact_group_members_unique UNIQUE (contact_id, group_id);


--
-- Name: contact_groups contact_groups_pkey; Type: CONSTRAINT; Schema: user_management; Owner: user_ai
--

ALTER TABLE ONLY user_management.contact_groups
    ADD CONSTRAINT contact_groups_pkey PRIMARY KEY (id);


--
-- Name: contact_groups contact_groups_user_name_unique; Type: CONSTRAINT; Schema: user_management; Owner: user_ai
--

ALTER TABLE ONLY user_management.contact_groups
    ADD CONSTRAINT contact_groups_user_name_unique UNIQUE (user_id, name);


--
-- Name: contacts contacts_pkey; Type: CONSTRAINT; Schema: user_management; Owner: user_ai
--

ALTER TABLE ONLY user_management.contacts
    ADD CONSTRAINT contacts_pkey PRIMARY KEY (id);


--
-- Name: contacts contacts_user_phone_unique; Type: CONSTRAINT; Schema: user_management; Owner: user_ai
--

ALTER TABLE ONLY user_management.contacts
    ADD CONSTRAINT contacts_user_phone_unique UNIQUE (user_id, phone_number);


--
-- Name: user_settings user_settings_pkey; Type: CONSTRAINT; Schema: user_management; Owner: user_ai
--

ALTER TABLE ONLY user_management.user_settings
    ADD CONSTRAINT user_settings_pkey PRIMARY KEY (id);


--
-- Name: user_settings user_settings_user_unique; Type: CONSTRAINT; Schema: user_management; Owner: user_ai
--

ALTER TABLE ONLY user_management.user_settings
    ADD CONSTRAINT user_settings_user_unique UNIQUE (user_id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: user_management; Owner: user_ai
--

ALTER TABLE ONLY user_management.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_phone_number_key; Type: CONSTRAINT; Schema: user_management; Owner: user_ai
--

ALTER TABLE ONLY user_management.users
    ADD CONSTRAINT users_phone_number_key UNIQUE (phone_number);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: user_management; Owner: user_ai
--

ALTER TABLE ONLY user_management.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: idx_ai_instructions_status; Type: INDEX; Schema: ai_intelligence; Owner: user_ai
--

CREATE INDEX idx_ai_instructions_status ON ai_intelligence.ai_instructions USING btree (status);


--
-- Name: idx_ai_instructions_user; Type: INDEX; Schema: ai_intelligence; Owner: user_ai
--

CREATE INDEX idx_ai_instructions_user ON ai_intelligence.ai_instructions USING btree (user_id);


--
-- Name: idx_embeddings_type; Type: INDEX; Schema: ai_intelligence; Owner: user_ai
--

CREATE INDEX idx_embeddings_type ON ai_intelligence.embeddings USING btree (content_type);


--
-- Name: idx_embeddings_user_content; Type: INDEX; Schema: ai_intelligence; Owner: user_ai
--

CREATE INDEX idx_embeddings_user_content ON ai_intelligence.embeddings USING btree (user_id, content_type, content_id);


--
-- Name: idx_embeddings_vector; Type: INDEX; Schema: ai_intelligence; Owner: user_ai
--

CREATE INDEX idx_embeddings_vector ON ai_intelligence.embeddings USING ivfflat (embedding public.vector_cosine_ops) WITH (lists='100');


--
-- Name: idx_feed_items_active; Type: INDEX; Schema: ai_intelligence; Owner: user_ai
--

CREATE INDEX idx_feed_items_active ON ai_intelligence.feed_items USING btree (user_id, status, expires_at) WHERE (status = 'active'::text);


--
-- Name: idx_feed_items_embedding; Type: INDEX; Schema: ai_intelligence; Owner: user_ai
--

CREATE INDEX idx_feed_items_embedding ON ai_intelligence.feed_items USING ivfflat (embedding public.vector_cosine_ops) WITH (lists='100');


--
-- Name: idx_feed_items_priority; Type: INDEX; Schema: ai_intelligence; Owner: user_ai
--

CREATE INDEX idx_feed_items_priority ON ai_intelligence.feed_items USING btree (priority DESC, created_at DESC);


--
-- Name: idx_feed_items_status; Type: INDEX; Schema: ai_intelligence; Owner: user_ai
--

CREATE INDEX idx_feed_items_status ON ai_intelligence.feed_items USING btree (status, expires_at);


--
-- Name: idx_feed_items_tags; Type: INDEX; Schema: ai_intelligence; Owner: user_ai
--

CREATE INDEX idx_feed_items_tags ON ai_intelligence.feed_items USING gin (tags);


--
-- Name: idx_feed_items_user_id; Type: INDEX; Schema: ai_intelligence; Owner: user_ai
--

CREATE INDEX idx_feed_items_user_id ON ai_intelligence.feed_items USING btree (user_id);


--
-- Name: idx_labs_images_embed; Type: INDEX; Schema: ai_intelligence; Owner: user_ai
--

CREATE INDEX idx_labs_images_embed ON ai_intelligence.labs_images USING ivfflat (embedding public.vector_cosine_ops) WITH (lists='25');


--
-- Name: idx_labs_message_chunks_embed; Type: INDEX; Schema: ai_intelligence; Owner: user_ai
--

CREATE INDEX idx_labs_message_chunks_embed ON ai_intelligence.labs_message_chunks USING ivfflat (embedding public.vector_cosine_ops) WITH (lists='50');


--
-- Name: idx_labs_message_chunks_message; Type: INDEX; Schema: ai_intelligence; Owner: user_ai
--

CREATE INDEX idx_labs_message_chunks_message ON ai_intelligence.labs_message_chunks USING btree (message_id);


--
-- Name: idx_labs_messages_user; Type: INDEX; Schema: ai_intelligence; Owner: user_ai
--

CREATE INDEX idx_labs_messages_user ON ai_intelligence.labs_messages USING btree (user_id);


--
-- Name: idx_ml_model_metrics_date; Type: INDEX; Schema: ai_intelligence; Owner: user_ai
--

CREATE INDEX idx_ml_model_metrics_date ON ai_intelligence.ml_model_metrics USING btree (evaluation_date);


--
-- Name: idx_ml_model_metrics_model; Type: INDEX; Schema: ai_intelligence; Owner: user_ai
--

CREATE INDEX idx_ml_model_metrics_model ON ai_intelligence.ml_model_metrics USING btree (model_name, model_version);


--
-- Name: idx_policies_active; Type: INDEX; Schema: ai_intelligence; Owner: user_ai
--

CREATE INDEX idx_policies_active ON ai_intelligence.policies USING btree (user_id, is_active) WHERE (is_active = true);


--
-- Name: idx_policies_embedding; Type: INDEX; Schema: ai_intelligence; Owner: user_ai
--

CREATE INDEX idx_policies_embedding ON ai_intelligence.policies USING ivfflat (embedding public.vector_cosine_ops) WITH (lists='100');


--
-- Name: idx_policies_priority; Type: INDEX; Schema: ai_intelligence; Owner: user_ai
--

CREATE INDEX idx_policies_priority ON ai_intelligence.policies USING btree (priority DESC, created_at DESC);


--
-- Name: idx_policies_type; Type: INDEX; Schema: ai_intelligence; Owner: user_ai
--

CREATE INDEX idx_policies_type ON ai_intelligence.policies USING btree (policy_type);


--
-- Name: idx_policies_user_id; Type: INDEX; Schema: ai_intelligence; Owner: user_ai
--

CREATE INDEX idx_policies_user_id ON ai_intelligence.policies USING btree (user_id);


--
-- Name: idx_spam_patterns_active; Type: INDEX; Schema: ai_intelligence; Owner: user_ai
--

CREATE INDEX idx_spam_patterns_active ON ai_intelligence.spam_patterns USING btree (is_active, confidence_score) WHERE (is_active = true);


--
-- Name: idx_spam_patterns_type; Type: INDEX; Schema: ai_intelligence; Owner: user_ai
--

CREATE INDEX idx_spam_patterns_type ON ai_intelligence.spam_patterns USING btree (pattern_type);


--
-- Name: idx_spam_patterns_value; Type: INDEX; Schema: ai_intelligence; Owner: user_ai
--

CREATE INDEX idx_spam_patterns_value ON ai_intelligence.spam_patterns USING btree (pattern_value);


--
-- Name: idx_voice_models_active; Type: INDEX; Schema: ai_intelligence; Owner: user_ai
--

CREATE INDEX idx_voice_models_active ON ai_intelligence.voice_models USING btree (user_id, is_active) WHERE (is_active = true);


--
-- Name: idx_voice_models_user; Type: INDEX; Schema: ai_intelligence; Owner: user_ai
--

CREATE INDEX idx_voice_models_user ON ai_intelligence.voice_models USING btree (user_id);


--
-- Name: idx_ai_performance_metrics_type; Type: INDEX; Schema: analytics; Owner: user_ai
--

CREATE INDEX idx_ai_performance_metrics_type ON analytics.ai_performance_metrics USING btree (metric_type, metric_date);


--
-- Name: idx_ai_performance_metrics_user_date; Type: INDEX; Schema: analytics; Owner: user_ai
--

CREATE INDEX idx_ai_performance_metrics_user_date ON analytics.ai_performance_metrics USING btree (user_id, metric_date);


--
-- Name: idx_call_analytics_call_id; Type: INDEX; Schema: analytics; Owner: user_ai
--

CREATE INDEX idx_call_analytics_call_id ON analytics.call_analytics USING btree (call_id);


--
-- Name: idx_call_analytics_created; Type: INDEX; Schema: analytics; Owner: user_ai
--

CREATE INDEX idx_call_analytics_created ON analytics.call_analytics USING btree (created_at);


--
-- Name: idx_call_analytics_user_type; Type: INDEX; Schema: analytics; Owner: user_ai
--

CREATE INDEX idx_call_analytics_user_type ON analytics.call_analytics USING btree (user_id, analysis_type);


--
-- Name: idx_contact_interaction_summary_user_contact; Type: INDEX; Schema: analytics; Owner: user_ai
--

CREATE INDEX idx_contact_interaction_summary_user_contact ON analytics.contact_interaction_summary USING btree (user_id, contact_id);


--
-- Name: idx_message_analytics_created; Type: INDEX; Schema: analytics; Owner: user_ai
--

CREATE INDEX idx_message_analytics_created ON analytics.message_analytics USING btree (created_at);


--
-- Name: idx_message_analytics_message_id; Type: INDEX; Schema: analytics; Owner: user_ai
--

CREATE INDEX idx_message_analytics_message_id ON analytics.message_analytics USING btree (message_id);


--
-- Name: idx_message_analytics_user_type; Type: INDEX; Schema: analytics; Owner: user_ai
--

CREATE INDEX idx_message_analytics_user_type ON analytics.message_analytics USING btree (user_id, analysis_type);


--
-- Name: idx_monthly_reports_date_range; Type: INDEX; Schema: analytics; Owner: user_ai
--

CREATE INDEX idx_monthly_reports_date_range ON analytics.monthly_reports USING btree (start_date, end_date);


--
-- Name: idx_monthly_reports_user_month; Type: INDEX; Schema: analytics; Owner: user_ai
--

CREATE INDEX idx_monthly_reports_user_month ON analytics.monthly_reports USING btree (user_id, report_month);


--
-- Name: idx_usage_statistics_date; Type: INDEX; Schema: analytics; Owner: user_ai
--

CREATE INDEX idx_usage_statistics_date ON analytics.usage_statistics USING btree (stat_date);


--
-- Name: idx_usage_statistics_user_date; Type: INDEX; Schema: analytics; Owner: user_ai
--

CREATE INDEX idx_usage_statistics_user_date ON analytics.usage_statistics USING btree (user_id, stat_date);


--
-- Name: idx_user_activity_logs_ip; Type: INDEX; Schema: analytics; Owner: user_ai
--

CREATE INDEX idx_user_activity_logs_ip ON analytics.user_activity_logs USING btree (ip_address, created_at);


--
-- Name: idx_user_activity_logs_session; Type: INDEX; Schema: analytics; Owner: user_ai
--

CREATE INDEX idx_user_activity_logs_session ON analytics.user_activity_logs USING btree (session_id) WHERE (session_id IS NOT NULL);


--
-- Name: idx_user_activity_logs_type; Type: INDEX; Schema: analytics; Owner: user_ai
--

CREATE INDEX idx_user_activity_logs_type ON analytics.user_activity_logs USING btree (activity_type, created_at);


--
-- Name: idx_user_activity_logs_user_time; Type: INDEX; Schema: analytics; Owner: user_ai
--

CREATE INDEX idx_user_activity_logs_user_time ON analytics.user_activity_logs USING btree (user_id, created_at);


--
-- Name: idx_weekly_reports_date_range; Type: INDEX; Schema: analytics; Owner: user_ai
--

CREATE INDEX idx_weekly_reports_date_range ON analytics.weekly_reports USING btree (start_date, end_date);


--
-- Name: idx_weekly_reports_user_week; Type: INDEX; Schema: analytics; Owner: user_ai
--

CREATE INDEX idx_weekly_reports_user_week ON analytics.weekly_reports USING btree (user_id, report_week);


--
-- Name: idx_calls_contact_id; Type: INDEX; Schema: communication; Owner: user_ai
--

CREATE INDEX idx_calls_contact_id ON communication.calls USING btree (contact_id);


--
-- Name: idx_calls_direction; Type: INDEX; Schema: communication; Owner: user_ai
--

CREATE INDEX idx_calls_direction ON communication.calls USING btree (direction);


--
-- Name: idx_calls_from_number; Type: INDEX; Schema: communication; Owner: user_ai
--

CREATE INDEX idx_calls_from_number ON communication.calls USING btree (from_number);


--
-- Name: idx_calls_spam; Type: INDEX; Schema: communication; Owner: user_ai
--

CREATE INDEX idx_calls_spam ON communication.calls USING btree (is_spam, spam_score) WHERE (is_spam = true);


--
-- Name: idx_calls_started_at; Type: INDEX; Schema: communication; Owner: user_ai
--

CREATE INDEX idx_calls_started_at ON communication.calls USING btree (started_at);


--
-- Name: idx_calls_status; Type: INDEX; Schema: communication; Owner: user_ai
--

CREATE INDEX idx_calls_status ON communication.calls USING btree (status);


--
-- Name: idx_calls_user_date; Type: INDEX; Schema: communication; Owner: user_ai
--

CREATE INDEX idx_calls_user_date ON communication.calls USING btree (user_id, started_at);


--
-- Name: idx_calls_user_id; Type: INDEX; Schema: communication; Owner: user_ai
--

CREATE INDEX idx_calls_user_id ON communication.calls USING btree (user_id);


--
-- Name: idx_conversation_contexts_active; Type: INDEX; Schema: communication; Owner: user_ai
--

CREATE INDEX idx_conversation_contexts_active ON communication.conversation_contexts USING btree (is_active, start_time) WHERE (is_active = true);


--
-- Name: idx_conversation_contexts_conversation_id; Type: INDEX; Schema: communication; Owner: user_ai
--

CREATE INDEX idx_conversation_contexts_conversation_id ON communication.conversation_contexts USING btree (conversation_id);


--
-- Name: idx_conversation_contexts_user_id; Type: INDEX; Schema: communication; Owner: user_ai
--

CREATE INDEX idx_conversation_contexts_user_id ON communication.conversation_contexts USING btree (user_id);


--
-- Name: idx_messages_body_search; Type: INDEX; Schema: communication; Owner: user_ai
--

CREATE INDEX idx_messages_body_search ON communication.messages USING gin (to_tsvector('english'::regconfig, message_body));


--
-- Name: idx_messages_contact_id; Type: INDEX; Schema: communication; Owner: user_ai
--

CREATE INDEX idx_messages_contact_id ON communication.messages USING btree (contact_id);


--
-- Name: idx_messages_conversation_id; Type: INDEX; Schema: communication; Owner: user_ai
--

CREATE INDEX idx_messages_conversation_id ON communication.messages USING btree (conversation_id);


--
-- Name: idx_messages_direction; Type: INDEX; Schema: communication; Owner: user_ai
--

CREATE INDEX idx_messages_direction ON communication.messages USING btree (direction);


--
-- Name: idx_messages_phone_number; Type: INDEX; Schema: communication; Owner: user_ai
--

CREATE INDEX idx_messages_phone_number ON communication.messages USING btree (phone_number);


--
-- Name: idx_messages_received_at; Type: INDEX; Schema: communication; Owner: user_ai
--

CREATE INDEX idx_messages_received_at ON communication.messages USING btree (received_at);


--
-- Name: idx_messages_spam; Type: INDEX; Schema: communication; Owner: user_ai
--

CREATE INDEX idx_messages_spam ON communication.messages USING btree (is_spam, spam_score) WHERE (is_spam = true);


--
-- Name: idx_messages_unread; Type: INDEX; Schema: communication; Owner: user_ai
--

CREATE INDEX idx_messages_unread ON communication.messages USING btree (user_id, is_read, received_at) WHERE (is_read = false);


--
-- Name: idx_messages_user_id; Type: INDEX; Schema: communication; Owner: user_ai
--

CREATE INDEX idx_messages_user_id ON communication.messages USING btree (user_id);


--
-- Name: idx_deletion_log_document; Type: INDEX; Schema: data_feeds; Owner: user_ai
--

CREATE INDEX idx_deletion_log_document ON data_feeds.document_deletion_log USING btree (document_id);


--
-- Name: idx_deletion_log_user; Type: INDEX; Schema: data_feeds; Owner: user_ai
--

CREATE INDEX idx_deletion_log_user ON data_feeds.document_deletion_log USING btree (deleted_by, deleted_at DESC);


--
-- Name: idx_document_versions_document; Type: INDEX; Schema: data_feeds; Owner: user_ai
--

CREATE INDEX idx_document_versions_document ON data_feeds.document_versions USING btree (document_id, version DESC);


--
-- Name: idx_documents_deleted; Type: INDEX; Schema: data_feeds; Owner: user_ai
--

CREATE INDEX idx_documents_deleted ON data_feeds.documents USING btree (user_id, deleted_at) WHERE (is_deleted = true);


--
-- Name: idx_documents_embedding; Type: INDEX; Schema: data_feeds; Owner: user_ai
--

CREATE INDEX idx_documents_embedding ON data_feeds.documents USING ivfflat (embedding public.vector_cosine_ops) WITH (lists='100');


--
-- Name: idx_documents_file_type; Type: INDEX; Schema: data_feeds; Owner: user_ai
--

CREATE INDEX idx_documents_file_type ON data_feeds.documents USING btree (file_type);


--
-- Name: idx_documents_not_deleted; Type: INDEX; Schema: data_feeds; Owner: user_ai
--

CREATE INDEX idx_documents_not_deleted ON data_feeds.documents USING btree (user_id, is_deleted) WHERE (is_deleted = false);


--
-- Name: idx_documents_user_file_type; Type: INDEX; Schema: data_feeds; Owner: user_ai
--

CREATE INDEX idx_documents_user_file_type ON data_feeds.documents USING btree (user_id, file_type);


--
-- Name: idx_documents_version; Type: INDEX; Schema: data_feeds; Owner: user_ai
--

CREATE INDEX idx_documents_version ON data_feeds.documents USING btree (user_id, version);


--
-- Name: idx_concepts_file; Type: INDEX; Schema: data_feeds_metadata; Owner: user_ai
--

CREATE INDEX idx_concepts_file ON data_feeds_metadata.concepts USING btree (file_id, concept_type);


--
-- Name: idx_concepts_type; Type: INDEX; Schema: data_feeds_metadata; Owner: user_ai
--

CREATE INDEX idx_concepts_type ON data_feeds_metadata.concepts USING btree (concept_type, is_active);


--
-- Name: idx_concepts_value; Type: INDEX; Schema: data_feeds_metadata; Owner: user_ai
--

CREATE INDEX idx_concepts_value ON data_feeds_metadata.concepts USING btree (concept_value);


--
-- Name: idx_vector_mappings_file; Type: INDEX; Schema: data_feeds_metadata; Owner: user_ai
--

CREATE INDEX idx_vector_mappings_file ON data_feeds_metadata.vector_mappings USING btree (file_id);


--
-- Name: idx_vector_mappings_key; Type: INDEX; Schema: data_feeds_metadata; Owner: user_ai
--

CREATE INDEX idx_vector_mappings_key ON data_feeds_metadata.vector_mappings USING btree (vector_key);


--
-- Name: idx_embeddings_active; Type: INDEX; Schema: data_feeds_vectors; Owner: user_ai
--

CREATE INDEX idx_embeddings_active ON data_feeds_vectors.embeddings USING btree (is_active) WHERE (is_active = true);


--
-- Name: idx_embeddings_file; Type: INDEX; Schema: data_feeds_vectors; Owner: user_ai
--

CREATE INDEX idx_embeddings_file ON data_feeds_vectors.embeddings USING btree (file_id, is_active);


--
-- Name: idx_embeddings_vector; Type: INDEX; Schema: data_feeds_vectors; Owner: user_ai
--

CREATE INDEX idx_embeddings_vector ON data_feeds_vectors.embeddings USING ivfflat (embedding public.vector_cosine_ops) WITH (lists='100');


--
-- Name: idx_contact_group_members_contact; Type: INDEX; Schema: user_management; Owner: user_ai
--

CREATE INDEX idx_contact_group_members_contact ON user_management.contact_group_members USING btree (contact_id);


--
-- Name: idx_contact_group_members_group; Type: INDEX; Schema: user_management; Owner: user_ai
--

CREATE INDEX idx_contact_group_members_group ON user_management.contact_group_members USING btree (group_id);


--
-- Name: idx_contact_groups_user; Type: INDEX; Schema: user_management; Owner: user_ai
--

CREATE INDEX idx_contact_groups_user ON user_management.contact_groups USING btree (user_id);


--
-- Name: idx_contacts_blocked; Type: INDEX; Schema: user_management; Owner: user_ai
--

CREATE INDEX idx_contacts_blocked ON user_management.contacts USING btree (user_id, is_blocked) WHERE (is_blocked = true);


--
-- Name: idx_contacts_phone; Type: INDEX; Schema: user_management; Owner: user_ai
--

CREATE INDEX idx_contacts_phone ON user_management.contacts USING btree (phone_number);


--
-- Name: idx_contacts_user_id; Type: INDEX; Schema: user_management; Owner: user_ai
--

CREATE INDEX idx_contacts_user_id ON user_management.contacts USING btree (user_id);


--
-- Name: idx_contacts_user_phone; Type: INDEX; Schema: user_management; Owner: user_ai
--

CREATE INDEX idx_contacts_user_phone ON user_management.contacts USING btree (user_id, phone_number);


--
-- Name: idx_contacts_whitelisted; Type: INDEX; Schema: user_management; Owner: user_ai
--

CREATE INDEX idx_contacts_whitelisted ON user_management.contacts USING btree (user_id, is_whitelisted) WHERE (is_whitelisted = true);


--
-- Name: idx_user_settings_user_id; Type: INDEX; Schema: user_management; Owner: user_ai
--

CREATE INDEX idx_user_settings_user_id ON user_management.user_settings USING btree (user_id);


--
-- Name: idx_users_account_status; Type: INDEX; Schema: user_management; Owner: user_ai
--

CREATE INDEX idx_users_account_status ON user_management.users USING btree (account_status);


--
-- Name: idx_users_active; Type: INDEX; Schema: user_management; Owner: user_ai
--

CREATE INDEX idx_users_active ON user_management.users USING btree (is_active, created_at);


--
-- Name: idx_users_active_email; Type: INDEX; Schema: user_management; Owner: user_ai
--

CREATE INDEX idx_users_active_email ON user_management.users USING btree (is_active, email) WHERE (is_active = true);


--
-- Name: idx_users_consent; Type: INDEX; Schema: user_management; Owner: user_ai
--

CREATE INDEX idx_users_consent ON user_management.users USING btree (data_processing_consent, consent_given_at);


--
-- Name: idx_users_deleted_at; Type: INDEX; Schema: user_management; Owner: user_ai
--

CREATE INDEX idx_users_deleted_at ON user_management.users USING btree (deleted_at);


--
-- Name: idx_users_email; Type: INDEX; Schema: user_management; Owner: user_ai
--

CREATE INDEX idx_users_email ON user_management.users USING btree (email);


--
-- Name: idx_users_email_verification_token; Type: INDEX; Schema: user_management; Owner: user_ai
--

CREATE INDEX idx_users_email_verification_token ON user_management.users USING btree (email_verification_token);


--
-- Name: idx_users_last_activity; Type: INDEX; Schema: user_management; Owner: user_ai
--

CREATE INDEX idx_users_last_activity ON user_management.users USING btree (last_activity_at);


--
-- Name: idx_users_locked_until; Type: INDEX; Schema: user_management; Owner: user_ai
--

CREATE INDEX idx_users_locked_until ON user_management.users USING btree (locked_until);


--
-- Name: idx_users_name; Type: INDEX; Schema: user_management; Owner: user_ai
--

CREATE INDEX idx_users_name ON user_management.users USING btree (name);


--
-- Name: idx_users_password_reset_token; Type: INDEX; Schema: user_management; Owner: user_ai
--

CREATE INDEX idx_users_password_reset_token ON user_management.users USING btree (password_reset_token);


--
-- Name: idx_users_phone; Type: INDEX; Schema: user_management; Owner: user_ai
--

CREATE INDEX idx_users_phone ON user_management.users USING btree (phone_number);


--
-- Name: idx_users_phone_verification_token; Type: INDEX; Schema: user_management; Owner: user_ai
--

CREATE INDEX idx_users_phone_verification_token ON user_management.users USING btree (phone_verification_token);


--
-- Name: idx_users_privacy_level; Type: INDEX; Schema: user_management; Owner: user_ai
--

CREATE INDEX idx_users_privacy_level ON user_management.users USING btree (privacy_level);


--
-- Name: idx_users_search; Type: INDEX; Schema: user_management; Owner: user_ai
--

CREATE INDEX idx_users_search ON user_management.users USING gin (to_tsvector('english'::regconfig, ((COALESCE(name, ''::text) || ' '::text) || COALESCE(email, ''::text))));


--
-- Name: idx_users_status_created; Type: INDEX; Schema: user_management; Owner: user_ai
--

CREATE INDEX idx_users_status_created ON user_management.users USING btree (account_status, created_at);


--
-- Name: idx_users_verified; Type: INDEX; Schema: user_management; Owner: user_ai
--

CREATE INDEX idx_users_verified ON user_management.users USING btree (email_verified, phone_verified);


--
-- Name: idx_users_version; Type: INDEX; Schema: user_management; Owner: user_ai
--

CREATE INDEX idx_users_version ON user_management.users USING btree (version);


--
-- Name: ai_instructions ai_instructions_user_id_fkey; Type: FK CONSTRAINT; Schema: ai_intelligence; Owner: user_ai
--

ALTER TABLE ONLY ai_intelligence.ai_instructions
    ADD CONSTRAINT ai_instructions_user_id_fkey FOREIGN KEY (user_id) REFERENCES user_management.users(id) ON DELETE CASCADE;


--
-- Name: embeddings embeddings_user_id_fkey; Type: FK CONSTRAINT; Schema: ai_intelligence; Owner: user_ai
--

ALTER TABLE ONLY ai_intelligence.embeddings
    ADD CONSTRAINT embeddings_user_id_fkey FOREIGN KEY (user_id) REFERENCES user_management.users(id) ON DELETE CASCADE;


--
-- Name: feed_items feed_items_user_id_fkey; Type: FK CONSTRAINT; Schema: ai_intelligence; Owner: user_ai
--

ALTER TABLE ONLY ai_intelligence.feed_items
    ADD CONSTRAINT feed_items_user_id_fkey FOREIGN KEY (user_id) REFERENCES user_management.users(id) ON DELETE CASCADE;


--
-- Name: labs_images labs_images_user_id_fkey; Type: FK CONSTRAINT; Schema: ai_intelligence; Owner: user_ai
--

ALTER TABLE ONLY ai_intelligence.labs_images
    ADD CONSTRAINT labs_images_user_id_fkey FOREIGN KEY (user_id) REFERENCES user_management.users(id) ON DELETE SET NULL;


--
-- Name: labs_message_chunks labs_message_chunks_message_id_fkey; Type: FK CONSTRAINT; Schema: ai_intelligence; Owner: user_ai
--

ALTER TABLE ONLY ai_intelligence.labs_message_chunks
    ADD CONSTRAINT labs_message_chunks_message_id_fkey FOREIGN KEY (message_id) REFERENCES ai_intelligence.labs_messages(message_id) ON DELETE CASCADE;


--
-- Name: labs_messages labs_messages_user_id_fkey; Type: FK CONSTRAINT; Schema: ai_intelligence; Owner: user_ai
--

ALTER TABLE ONLY ai_intelligence.labs_messages
    ADD CONSTRAINT labs_messages_user_id_fkey FOREIGN KEY (user_id) REFERENCES user_management.users(id) ON DELETE SET NULL;


--
-- Name: policies policies_user_id_fkey; Type: FK CONSTRAINT; Schema: ai_intelligence; Owner: user_ai
--

ALTER TABLE ONLY ai_intelligence.policies
    ADD CONSTRAINT policies_user_id_fkey FOREIGN KEY (user_id) REFERENCES user_management.users(id) ON DELETE CASCADE;


--
-- Name: spam_patterns spam_patterns_created_by_fkey; Type: FK CONSTRAINT; Schema: ai_intelligence; Owner: user_ai
--

ALTER TABLE ONLY ai_intelligence.spam_patterns
    ADD CONSTRAINT spam_patterns_created_by_fkey FOREIGN KEY (created_by) REFERENCES user_management.users(id) ON DELETE SET NULL;


--
-- Name: voice_models voice_models_user_id_fkey; Type: FK CONSTRAINT; Schema: ai_intelligence; Owner: user_ai
--

ALTER TABLE ONLY ai_intelligence.voice_models
    ADD CONSTRAINT voice_models_user_id_fkey FOREIGN KEY (user_id) REFERENCES user_management.users(id) ON DELETE CASCADE;


--
-- Name: ai_performance_metrics ai_performance_metrics_user_id_fkey; Type: FK CONSTRAINT; Schema: analytics; Owner: user_ai
--

ALTER TABLE ONLY analytics.ai_performance_metrics
    ADD CONSTRAINT ai_performance_metrics_user_id_fkey FOREIGN KEY (user_id) REFERENCES user_management.users(id) ON DELETE CASCADE;


--
-- Name: call_analytics call_analytics_call_id_fkey; Type: FK CONSTRAINT; Schema: analytics; Owner: user_ai
--

ALTER TABLE ONLY analytics.call_analytics
    ADD CONSTRAINT call_analytics_call_id_fkey FOREIGN KEY (call_id) REFERENCES communication.calls(id) ON DELETE CASCADE;


--
-- Name: call_analytics call_analytics_user_id_fkey; Type: FK CONSTRAINT; Schema: analytics; Owner: user_ai
--

ALTER TABLE ONLY analytics.call_analytics
    ADD CONSTRAINT call_analytics_user_id_fkey FOREIGN KEY (user_id) REFERENCES user_management.users(id) ON DELETE CASCADE;


--
-- Name: contact_interaction_summary contact_interaction_summary_contact_id_fkey; Type: FK CONSTRAINT; Schema: analytics; Owner: user_ai
--

ALTER TABLE ONLY analytics.contact_interaction_summary
    ADD CONSTRAINT contact_interaction_summary_contact_id_fkey FOREIGN KEY (contact_id) REFERENCES user_management.contacts(id) ON DELETE CASCADE;


--
-- Name: contact_interaction_summary contact_interaction_summary_user_id_fkey; Type: FK CONSTRAINT; Schema: analytics; Owner: user_ai
--

ALTER TABLE ONLY analytics.contact_interaction_summary
    ADD CONSTRAINT contact_interaction_summary_user_id_fkey FOREIGN KEY (user_id) REFERENCES user_management.users(id) ON DELETE CASCADE;


--
-- Name: message_analytics message_analytics_message_id_fkey; Type: FK CONSTRAINT; Schema: analytics; Owner: user_ai
--

ALTER TABLE ONLY analytics.message_analytics
    ADD CONSTRAINT message_analytics_message_id_fkey FOREIGN KEY (message_id) REFERENCES communication.messages(id) ON DELETE CASCADE;


--
-- Name: message_analytics message_analytics_user_id_fkey; Type: FK CONSTRAINT; Schema: analytics; Owner: user_ai
--

ALTER TABLE ONLY analytics.message_analytics
    ADD CONSTRAINT message_analytics_user_id_fkey FOREIGN KEY (user_id) REFERENCES user_management.users(id) ON DELETE CASCADE;


--
-- Name: monthly_reports monthly_reports_user_id_fkey; Type: FK CONSTRAINT; Schema: analytics; Owner: user_ai
--

ALTER TABLE ONLY analytics.monthly_reports
    ADD CONSTRAINT monthly_reports_user_id_fkey FOREIGN KEY (user_id) REFERENCES user_management.users(id) ON DELETE CASCADE;


--
-- Name: usage_statistics usage_statistics_user_id_fkey; Type: FK CONSTRAINT; Schema: analytics; Owner: user_ai
--

ALTER TABLE ONLY analytics.usage_statistics
    ADD CONSTRAINT usage_statistics_user_id_fkey FOREIGN KEY (user_id) REFERENCES user_management.users(id) ON DELETE CASCADE;


--
-- Name: user_activity_logs user_activity_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: analytics; Owner: user_ai
--

ALTER TABLE ONLY analytics.user_activity_logs
    ADD CONSTRAINT user_activity_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES user_management.users(id) ON DELETE CASCADE;


--
-- Name: weekly_reports weekly_reports_user_id_fkey; Type: FK CONSTRAINT; Schema: analytics; Owner: user_ai
--

ALTER TABLE ONLY analytics.weekly_reports
    ADD CONSTRAINT weekly_reports_user_id_fkey FOREIGN KEY (user_id) REFERENCES user_management.users(id) ON DELETE CASCADE;


--
-- Name: calls calls_contact_id_fkey; Type: FK CONSTRAINT; Schema: communication; Owner: user_ai
--

ALTER TABLE ONLY communication.calls
    ADD CONSTRAINT calls_contact_id_fkey FOREIGN KEY (contact_id) REFERENCES user_management.contacts(id) ON DELETE SET NULL;


--
-- Name: calls calls_user_id_fkey; Type: FK CONSTRAINT; Schema: communication; Owner: user_ai
--

ALTER TABLE ONLY communication.calls
    ADD CONSTRAINT calls_user_id_fkey FOREIGN KEY (user_id) REFERENCES user_management.users(id) ON DELETE CASCADE;


--
-- Name: conversation_contexts conversation_contexts_user_id_fkey; Type: FK CONSTRAINT; Schema: communication; Owner: user_ai
--

ALTER TABLE ONLY communication.conversation_contexts
    ADD CONSTRAINT conversation_contexts_user_id_fkey FOREIGN KEY (user_id) REFERENCES user_management.users(id) ON DELETE CASCADE;


--
-- Name: messages messages_contact_id_fkey; Type: FK CONSTRAINT; Schema: communication; Owner: user_ai
--

ALTER TABLE ONLY communication.messages
    ADD CONSTRAINT messages_contact_id_fkey FOREIGN KEY (contact_id) REFERENCES user_management.contacts(id) ON DELETE SET NULL;


--
-- Name: messages messages_user_id_fkey; Type: FK CONSTRAINT; Schema: communication; Owner: user_ai
--

ALTER TABLE ONLY communication.messages
    ADD CONSTRAINT messages_user_id_fkey FOREIGN KEY (user_id) REFERENCES user_management.users(id) ON DELETE CASCADE;


--
-- Name: document_access_rules document_access_rules_document_id_fkey; Type: FK CONSTRAINT; Schema: data_feeds; Owner: user_ai
--

ALTER TABLE ONLY data_feeds.document_access_rules
    ADD CONSTRAINT document_access_rules_document_id_fkey FOREIGN KEY (document_id) REFERENCES data_feeds.documents(id) ON DELETE CASCADE;


--
-- Name: document_deletion_log document_deletion_log_deleted_by_fkey; Type: FK CONSTRAINT; Schema: data_feeds; Owner: user_ai
--

ALTER TABLE ONLY data_feeds.document_deletion_log
    ADD CONSTRAINT document_deletion_log_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES user_management.users(id);


--
-- Name: document_deletion_log document_deletion_log_document_id_fkey; Type: FK CONSTRAINT; Schema: data_feeds; Owner: user_ai
--

ALTER TABLE ONLY data_feeds.document_deletion_log
    ADD CONSTRAINT document_deletion_log_document_id_fkey FOREIGN KEY (document_id) REFERENCES data_feeds.documents(id);


--
-- Name: document_versions document_versions_created_by_fkey; Type: FK CONSTRAINT; Schema: data_feeds; Owner: user_ai
--

ALTER TABLE ONLY data_feeds.document_versions
    ADD CONSTRAINT document_versions_created_by_fkey FOREIGN KEY (created_by) REFERENCES user_management.users(id);


--
-- Name: document_versions document_versions_document_id_fkey; Type: FK CONSTRAINT; Schema: data_feeds; Owner: user_ai
--

ALTER TABLE ONLY data_feeds.document_versions
    ADD CONSTRAINT document_versions_document_id_fkey FOREIGN KEY (document_id) REFERENCES data_feeds.documents(id) ON DELETE CASCADE;


--
-- Name: documents documents_deleted_by_fkey; Type: FK CONSTRAINT; Schema: data_feeds; Owner: user_ai
--

ALTER TABLE ONLY data_feeds.documents
    ADD CONSTRAINT documents_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES user_management.users(id);


--
-- Name: documents documents_user_id_fkey; Type: FK CONSTRAINT; Schema: data_feeds; Owner: user_ai
--

ALTER TABLE ONLY data_feeds.documents
    ADD CONSTRAINT documents_user_id_fkey FOREIGN KEY (user_id) REFERENCES user_management.users(id) ON DELETE CASCADE;


--
-- Name: instruction_document_links instruction_document_links_document_id_fkey; Type: FK CONSTRAINT; Schema: data_feeds; Owner: user_ai
--

ALTER TABLE ONLY data_feeds.instruction_document_links
    ADD CONSTRAINT instruction_document_links_document_id_fkey FOREIGN KEY (document_id) REFERENCES data_feeds.documents(id) ON DELETE CASCADE;


--
-- Name: instruction_document_links instruction_document_links_instruction_id_fkey; Type: FK CONSTRAINT; Schema: data_feeds; Owner: user_ai
--

ALTER TABLE ONLY data_feeds.instruction_document_links
    ADD CONSTRAINT instruction_document_links_instruction_id_fkey FOREIGN KEY (instruction_id) REFERENCES ai_intelligence.ai_instructions(id);


--
-- Name: contact_group_members contact_group_members_contact_id_fkey; Type: FK CONSTRAINT; Schema: user_management; Owner: user_ai
--

ALTER TABLE ONLY user_management.contact_group_members
    ADD CONSTRAINT contact_group_members_contact_id_fkey FOREIGN KEY (contact_id) REFERENCES user_management.contacts(id) ON DELETE CASCADE;


--
-- Name: contact_group_members contact_group_members_group_id_fkey; Type: FK CONSTRAINT; Schema: user_management; Owner: user_ai
--

ALTER TABLE ONLY user_management.contact_group_members
    ADD CONSTRAINT contact_group_members_group_id_fkey FOREIGN KEY (group_id) REFERENCES user_management.contact_groups(id) ON DELETE CASCADE;


--
-- Name: contact_groups contact_groups_user_id_fkey; Type: FK CONSTRAINT; Schema: user_management; Owner: user_ai
--

ALTER TABLE ONLY user_management.contact_groups
    ADD CONSTRAINT contact_groups_user_id_fkey FOREIGN KEY (user_id) REFERENCES user_management.users(id) ON DELETE CASCADE;


--
-- Name: contacts contacts_user_id_fkey; Type: FK CONSTRAINT; Schema: user_management; Owner: user_ai
--

ALTER TABLE ONLY user_management.contacts
    ADD CONSTRAINT contacts_user_id_fkey FOREIGN KEY (user_id) REFERENCES user_management.users(id) ON DELETE CASCADE;


--
-- Name: user_settings user_settings_user_id_fkey; Type: FK CONSTRAINT; Schema: user_management; Owner: user_ai
--

ALTER TABLE ONLY user_management.user_settings
    ADD CONSTRAINT user_settings_user_id_fkey FOREIGN KEY (user_id) REFERENCES user_management.users(id) ON DELETE CASCADE;


--
-- Name: SCHEMA data_feeds; Type: ACL; Schema: -; Owner: user_ai
--

GRANT USAGE ON SCHEMA data_feeds TO PUBLIC;


--
-- Name: SCHEMA data_feeds_metadata; Type: ACL; Schema: -; Owner: user_ai
--

GRANT USAGE ON SCHEMA data_feeds_metadata TO PUBLIC;


--
-- Name: SCHEMA data_feeds_vectors; Type: ACL; Schema: -; Owner: user_ai
--

GRANT USAGE ON SCHEMA data_feeds_vectors TO PUBLIC;

-- Migration: add contact_notes and contact_interactions with proper FKs
-- This complements quellai-db_backup.sql where these tables are absent.

-- Contact notes
CREATE SCHEMA IF NOT EXISTS user_management;

CREATE TABLE IF NOT EXISTS user_management.contact_notes (
    id BIGSERIAL PRIMARY KEY,
    contact_id BIGINT NOT NULL,
    note_text TEXT NOT NULL,
    note_type VARCHAR(50) DEFAULT 'general',
    is_important BOOLEAN DEFAULT FALSE,
    is_private BOOLEAN DEFAULT FALSE,
    reminder_date TIMESTAMPTZ,
    tags JSONB,
    group_metadata JSONB,
    created_by VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);




ALTER TABLE  ONLY user_management.contact_notes
    ADD CONSTRAINT  contact_notes_contact_id_fkey
    FOREIGN KEY (contact_id)
    REFERENCES user_management.contacts(id)
    ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_contact_notes_contact
    ON user_management.contact_notes (contact_id);


-- Contact interactions (optional; used by ORM analytics)
CREATE TABLE IF NOT EXISTS user_management.contact_interactions (
    id BIGSERIAL PRIMARY KEY,
    contact_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    interaction_type VARCHAR(20) NOT NULL,
    direction VARCHAR(10) NOT NULL,
    duration_seconds INTEGER,
    status VARCHAR(20),
    summary TEXT,
    sentiment VARCHAR(20),
    importance_score DOUBLE PRECISION DEFAULT 0.0,
    follow_up_required BOOLEAN DEFAULT FALSE,
    follow_up_date TIMESTAMPTZ,
    tags JSONB,
    interaction_metadata JSONB,
    external_id VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE ONLY  user_management.contact_interactions
    ADD CONSTRAINT  contact_interactions_contact_id_fkey
    FOREIGN KEY (contact_id)
    REFERENCES user_management.contacts(id)
    ON DELETE CASCADE;

ALTER TABLE ONLY  user_management.contact_interactions
    ADD CONSTRAINT contact_interactions_user_id_fkey
    FOREIGN KEY (user_id)
    REFERENCES user_management.users(id)
    ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_interactions_contact
    ON user_management.contact_interactions (contact_id);
CREATE INDEX IF NOT EXISTS idx_interactions_user
    ON user_management.contact_interactions (user_id);
CREATE INDEX IF NOT EXISTS idx_interactions_type
    ON user_management.contact_interactions (interaction_type);
CREATE INDEX IF NOT EXISTS idx_interactions_date
    ON user_management.contact_interactions (created_at);
CREATE INDEX IF NOT EXISTS idx_interactions_follow_up
    ON user_management.contact_interactions (follow_up_required, follow_up_date);


-- Migration: add contact_relationships and contact_preferences with proper FKs

CREATE SCHEMA IF NOT EXISTS user_management;

-- contact_preferences
CREATE TABLE IF NOT EXISTS user_management.contact_preferences (
    id BIGSERIAL PRIMARY KEY,
    contact_id BIGINT NOT NULL,
    preference_type VARCHAR(50) NOT NULL,
    preference_key VARCHAR(100) NOT NULL,
    preference_value JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE ONLY user_management.contact_preferences
    ADD CONSTRAINT contact_preferences_contact_id_fkey
    FOREIGN KEY (contact_id)
    REFERENCES user_management.contacts(id)
    ON DELETE CASCADE;

CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_contact_preference
    ON user_management.contact_preferences (contact_id, preference_type, preference_key);


-- contact_relationships
CREATE TABLE IF NOT EXISTS user_management.contact_relationships (
    id BIGSERIAL PRIMARY KEY,
    contact_id BIGINT NOT NULL,
    related_contact_id BIGINT NOT NULL,
    relationship_type VARCHAR(50) NOT NULL,
    relationship_strength DOUBLE PRECISION DEFAULT 0.5,
    is_mutual BOOLEAN DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE ONLY user_management.contact_relationships
    ADD CONSTRAINT contact_relationships_contact_id_fkey
    FOREIGN KEY (contact_id)
    REFERENCES user_management.contacts(id)
    ON DELETE CASCADE;

ALTER TABLE ONLY user_management.contact_relationships
    ADD CONSTRAINT contact_relationships_related_contact_id_fkey
    FOREIGN KEY (related_contact_id)
    REFERENCES user_management.contacts(id)
    ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_contact_relationships_contact
    ON user_management.contact_relationships (contact_id);
CREATE INDEX IF NOT EXISTS idx_contact_relationships_related
    ON user_management.contact_relationships (related_contact_id);



--
-- PostgreSQL database dump complete
--

\unrestrict sBOhVppb0fGs7FssoclB9eiNpCdVaxntQ0ec8xkQBQN8ya9eXZipuvOKaBBkh6h


