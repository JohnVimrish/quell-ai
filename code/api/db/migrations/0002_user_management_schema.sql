
-- =============================================
-- USER MANAGEMENT SCHEMA
-- =============================================

CREATE TABLE IF NOT EXISTS user_management.users (
    id BIGSERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    phone_number TEXT UNIQUE,
    is_active BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT false,
    phone_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    last_login_at TIMESTAMPTZ,
    
    CONSTRAINT users_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'),
    CONSTRAINT users_phone_format CHECK (phone_number IS NULL OR phone_number ~ '^\+?[1-9]\d{1,14}')
);

CREATE TABLE IF NOT EXISTS user_management.user_settings (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES user_management.users(id) ON DELETE CASCADE,
    sms_forwarding_number TEXT,
    call_forwarding_number TEXT,
    ai_mode_enabled BOOLEAN DEFAULT true,
    ai_mode_expires_at TIMESTAMPTZ,
    spam_filtering_enabled BOOLEAN DEFAULT true,
    recording_enabled BOOLEAN DEFAULT false,
    transcript_enabled BOOLEAN DEFAULT false,
    voice_cloning_enabled BOOLEAN DEFAULT false,
    timezone TEXT DEFAULT 'UTC',
    language_code TEXT DEFAULT 'en',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    CONSTRAINT user_settings_user_unique UNIQUE(user_id),
    CONSTRAINT user_settings_timezone_valid CHECK (timezone IS NOT NULL),
    CONSTRAINT user_settings_language_valid CHECK (language_code ~ '^[a-z]{2}(-[A-Z]{2})?')
);

CREATE TABLE IF NOT EXISTS user_management.contacts (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES user_management.users(id) ON DELETE CASCADE,
    phone_number TEXT NOT NULL,
    display_name TEXT,
    first_name TEXT,
    last_name TEXT,
    email TEXT,
    avatar_url TEXT,
    is_blocked BOOLEAN DEFAULT false,
    is_whitelisted BOOLEAN DEFAULT false,
    is_archived BOOLEAN DEFAULT false,
    trust_level INTEGER DEFAULT 0 CHECK (trust_level BETWEEN -100 AND 100),
    last_interaction_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    CONSTRAINT contacts_user_phone_unique UNIQUE(user_id, phone_number),
    CONSTRAINT contacts_phone_format CHECK (phone_number ~ '^\+?[1-9]\d{1,14}'),
    CONSTRAINT contacts_email_format CHECK (email IS NULL OR email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
);

CREATE TABLE IF NOT EXISTS user_management.contact_groups (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES user_management.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    color_code TEXT DEFAULT '#007bff',
    created_at TIMESTAMPTZ DEFAULT now(),
    
    CONSTRAINT contact_groups_user_name_unique UNIQUE(user_id, name),
    CONSTRAINT contact_groups_color_format CHECK (color_code ~ '^#[0-9A-Fa-f]{6}')
);

CREATE TABLE IF NOT EXISTS user_management.contact_group_members (
    id BIGSERIAL PRIMARY KEY,
    contact_id BIGINT NOT NULL REFERENCES user_management.contacts(id) ON DELETE CASCADE,
    group_id BIGINT NOT NULL REFERENCES user_management.contact_groups(id) ON DELETE CASCADE,
    added_at TIMESTAMPTZ DEFAULT now(),
    
    CONSTRAINT contact_group_members_unique UNIQUE(contact_id, group_id)
);

-- Indexes for user_management schema
CREATE INDEX IF NOT EXISTS idx_users_email ON user_management.users(email);
CREATE INDEX IF NOT EXISTS idx_users_phone ON user_management.users(phone_number);
CREATE INDEX IF NOT EXISTS idx_users_active ON user_management.users(is_active, created_at);
CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_management.user_settings(user_id);
CREATE INDEX IF NOT EXISTS idx_contacts_user_id ON user_management.contacts(user_id);
CREATE INDEX IF NOT EXISTS idx_contacts_phone ON user_management.contacts(phone_number);
CREATE INDEX IF NOT EXISTS idx_contacts_user_phone ON user_management.contacts(user_id, phone_number);
CREATE INDEX IF NOT EXISTS idx_contacts_whitelisted ON user_management.contacts(user_id, is_whitelisted) WHERE is_whitelisted = true;
CREATE INDEX IF NOT EXISTS idx_contacts_blocked ON user_management.contacts(user_id, is_blocked) WHERE is_blocked = true;
CREATE INDEX IF NOT EXISTS idx_contact_groups_user ON user_management.contact_groups(user_id);
CREATE INDEX IF NOT EXISTS idx_contact_group_members_contact ON user_management.contact_group_members(contact_id);
CREATE INDEX IF NOT EXISTS idx_contact_group_members_group ON user_management.contact_group_members(group_id);
