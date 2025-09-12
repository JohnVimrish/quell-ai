-- api/db/migrations/0001_init.sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS users (
  id BIGSERIAL PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS contacts (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
  name TEXT,
  phone_e164 TEXT,
  priority INT DEFAULT 0,
  tags TEXT[]
);

CREATE TABLE IF NOT EXISTS feed_items (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  tags TEXT[],
  status TEXT CHECK (status IN ('active','fulfilled','archived')) DEFAULT 'active',
  created_at TIMESTAMPTZ DEFAULT now(),
  expires_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS policies (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  body_text TEXT NOT NULL,
  tags TEXT[],
  embedding vector(384)
);

CREATE TABLE IF NOT EXISTS calls (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
  from_number TEXT,
  started_at TIMESTAMPTZ DEFAULT now(),
  ended_at TIMESTAMPTZ,
  intent TEXT,
  urgency TEXT,
  outcome TEXT,
  transcript TEXT,
  recording_uri TEXT,
  policy_ids BIGINT[],
  spam_score INT
);

CREATE TABLE IF NOT EXISTS texts (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
  from_number TEXT,
  ts TIMESTAMPTZ DEFAULT now(),
  body TEXT,
  intent TEXT,
  outcome TEXT,
  spam_flag BOOLEAN DEFAULT false,
  convo_id TEXT
);

CREATE TABLE IF NOT EXISTS embeddings (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
  kind TEXT CHECK (kind IN ('policy','feed','history')),
  ref_id BIGINT,
  text TEXT NOT NULL,
  embedding vector(384)
);
