
-- Create schemas for logical separation
CREATE SCHEMA IF NOT EXISTS user_management;
CREATE SCHEMA IF NOT EXISTS communication;
CREATE SCHEMA IF NOT EXISTS ai_intelligence;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS system_config;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm; -- For text search optimization

-- Set search path to include all schemas
ALTER DATABASE quell_ai SET search_path TO user_management, communication, ai_intelligence, analytics, system_config, public;
