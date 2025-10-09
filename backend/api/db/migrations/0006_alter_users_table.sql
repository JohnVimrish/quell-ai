-- =============================================
-- ALTER USERS TABLE FOR AUTHENTICATION
-- =============================================

-- Add name column if it doesn't exist (for user display names)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'user_management' 
        AND table_name = 'users' 
        AND column_name = 'name'
    ) THEN
        ALTER TABLE user_management.users ADD COLUMN name TEXT;
    END IF;
END $$;

-- Update existing users to have a default name if NULL
UPDATE user_management.users 
SET name = COALESCE(name, SPLIT_PART(email, '@', 1))
WHERE name IS NULL;

-- Make name column NOT NULL after setting defaults
ALTER TABLE user_management.users ALTER COLUMN name SET NOT NULL;

-- Add index on name for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_name ON user_management.users(name);

-- Add constraint to ensure name is not empty
ALTER TABLE user_management.users 
ADD CONSTRAINT users_name_not_empty CHECK (LENGTH(TRIM(name)) > 0);

-- Add password reset token columns for future password reset functionality
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'user_management' 
        AND table_name = 'users' 
        AND column_name = 'password_reset_token'
    ) THEN
        ALTER TABLE user_management.users ADD COLUMN password_reset_token TEXT;
    END IF;
END $$;

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'user_management' 
        AND table_name = 'users' 
        AND column_name = 'password_reset_expires_at'
    ) THEN
        ALTER TABLE user_management.users ADD COLUMN password_reset_expires_at TIMESTAMPTZ;
    END IF;
END $$;

-- Add index on password reset token
CREATE INDEX IF NOT EXISTS idx_users_password_reset_token ON user_management.users(password_reset_token);

-- Add email verification token columns
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'user_management' 
        AND table_name = 'users' 
        AND column_name = 'email_verification_token'
    ) THEN
        ALTER TABLE user_management.users ADD COLUMN email_verification_token TEXT;
    END IF;
END $$;

-- Add phone verification token columns
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'user_management' 
        AND table_name = 'users' 
        AND column_name = 'phone_verification_token'
    ) THEN
        ALTER TABLE user_management.users ADD COLUMN phone_verification_token TEXT;
    END IF;
END $$;

-- Add indexes for verification tokens
CREATE INDEX IF NOT EXISTS idx_users_email_verification_token ON user_management.users(email_verification_token);
CREATE INDEX IF NOT EXISTS idx_users_phone_verification_token ON user_management.users(phone_verification_token);

-- Add account status tracking
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'user_management' 
        AND table_name = 'users' 
        AND column_name = 'account_status'
    ) THEN
        ALTER TABLE user_management.users ADD COLUMN account_status TEXT DEFAULT 'active' CHECK (account_status IN ('active', 'suspended', 'pending_verification', 'deleted'));
    END IF;
END $$;

-- Add failed login attempt tracking
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'user_management' 
        AND table_name = 'users' 
        AND column_name = 'failed_login_attempts'
    ) THEN
        ALTER TABLE user_management.users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0;
    END IF;
END $$;

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'user_management' 
        AND table_name = 'users' 
        AND column_name = 'locked_until'
    ) THEN
        ALTER TABLE user_management.users ADD COLUMN locked_until TIMESTAMPTZ;
    END IF;
END $$;

-- Add index on account status and locked_until for security queries
CREATE INDEX IF NOT EXISTS idx_users_account_status ON user_management.users(account_status);
CREATE INDEX IF NOT EXISTS idx_users_locked_until ON user_management.users(locked_until);

-- Add last activity tracking
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'user_management' 
        AND table_name = 'users' 
        AND column_name = 'last_activity_at'
    ) THEN
        ALTER TABLE user_management.users ADD COLUMN last_activity_at TIMESTAMPTZ;
    END IF;
END $$;

-- Add index on last activity
CREATE INDEX IF NOT EXISTS idx_users_last_activity ON user_management.users(last_activity_at);

-- Add timezone preference
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'user_management' 
        AND table_name = 'users' 
        AND column_name = 'timezone'
    ) THEN
        ALTER TABLE user_management.users ADD COLUMN timezone TEXT DEFAULT 'UTC';
    END IF;
END $$;

-- Add language preference
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'user_management' 
        AND table_name = 'users' 
        AND column_name = 'language_code'
    ) THEN
        ALTER TABLE user_management.users ADD COLUMN language_code TEXT DEFAULT 'en';
    END IF;
END $$;

-- Add constraints for timezone and language
ALTER TABLE user_management.users 
ADD CONSTRAINT users_timezone_valid CHECK (timezone IS NOT NULL);

ALTER TABLE user_management.users 
ADD CONSTRAINT users_language_valid CHECK (language_code ~ '^[a-z]{2}(-[A-Z]{2})?');

-- Add profile information
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'user_management' 
        AND table_name = 'users' 
        AND column_name = 'avatar_url'
    ) THEN
        ALTER TABLE user_management.users ADD COLUMN avatar_url TEXT;
    END IF;
END $$;

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'user_management' 
        AND table_name = 'users' 
        AND column_name = 'bio'
    ) THEN
        ALTER TABLE user_management.users ADD COLUMN bio TEXT;
    END IF;
END $$;

-- Add privacy settings
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'user_management' 
        AND table_name = 'users' 
        AND column_name = 'privacy_level'
    ) THEN
        ALTER TABLE user_management.users ADD COLUMN privacy_level TEXT DEFAULT 'standard' CHECK (privacy_level IN ('minimal', 'standard', 'enhanced', 'maximum'));
    END IF;
END $$;

-- Add index on privacy level
CREATE INDEX IF NOT EXISTS idx_users_privacy_level ON user_management.users(privacy_level);

-- Add notification preferences
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'user_management' 
        AND table_name = 'users' 
        AND column_name = 'email_notifications'
    ) THEN
        ALTER TABLE user_management.users ADD COLUMN email_notifications BOOLEAN DEFAULT true;
    END IF;
END $$;

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'user_management' 
        AND table_name = 'users' 
        AND column_name = 'sms_notifications'
    ) THEN
        ALTER TABLE user_management.users ADD COLUMN sms_notifications BOOLEAN DEFAULT false;
    END IF;
END $$;

-- Add marketing consent
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'user_management' 
        AND table_name = 'users' 
        AND column_name = 'marketing_consent'
    ) THEN
        ALTER TABLE user_management.users ADD COLUMN marketing_consent BOOLEAN DEFAULT false;
    END IF;
END $$;

-- Add data processing consent
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'user_management' 
        AND table_name = 'users' 
        AND column_name = 'data_processing_consent'
    ) THEN
        ALTER TABLE user_management.users ADD COLUMN data_processing_consent BOOLEAN DEFAULT false;
    END IF;
END $$;

-- Add consent timestamp
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'user_management' 
        AND table_name = 'users' 
        AND column_name = 'consent_given_at'
    ) THEN
        ALTER TABLE user_management.users ADD COLUMN consent_given_at TIMESTAMPTZ;
    END IF;
END $$;

-- Add index on consent
CREATE INDEX IF NOT EXISTS idx_users_consent ON user_management.users(data_processing_consent, consent_given_at);

-- Add audit trail columns
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'user_management' 
        AND table_name = 'users' 
        AND column_name = 'created_by'
    ) THEN
        ALTER TABLE user_management.users ADD COLUMN created_by TEXT DEFAULT 'system';
    END IF;
END $$;

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'user_management' 
        AND table_name = 'users' 
        AND column_name = 'updated_by'
    ) THEN
        ALTER TABLE user_management.users ADD COLUMN updated_by TEXT DEFAULT 'system';
    END IF;
END $$;

-- Add soft delete functionality
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'user_management' 
        AND table_name = 'users' 
        AND column_name = 'deleted_at'
    ) THEN
        ALTER TABLE user_management.users ADD COLUMN deleted_at TIMESTAMPTZ;
    END IF;
END $$;

-- Add index on deleted_at for soft delete queries
CREATE INDEX IF NOT EXISTS idx_users_deleted_at ON user_management.users(deleted_at);

-- Add constraint to ensure deleted users have deleted_at set
ALTER TABLE user_management.users 
ADD CONSTRAINT users_deleted_consistency CHECK (
    (account_status = 'deleted' AND deleted_at IS NOT NULL) OR 
    (account_status != 'deleted' AND deleted_at IS NULL)
);

-- Add version tracking for optimistic locking
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'user_management' 
        AND table_name = 'users' 
        AND column_name = 'version'
    ) THEN
        ALTER TABLE user_management.users ADD COLUMN version INTEGER DEFAULT 1;
    END IF;
END $$;

-- Add index on version
CREATE INDEX IF NOT EXISTS idx_users_version ON user_management.users(version);

-- Add full-text search index on name and email
CREATE INDEX IF NOT EXISTS idx_users_search ON user_management.users USING gin(
    to_tsvector('english', COALESCE(name, '') || ' ' || COALESCE(email, ''))
);

-- Add composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_users_active_email ON user_management.users(is_active, email) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_users_status_created ON user_management.users(account_status, created_at);
CREATE INDEX IF NOT EXISTS idx_users_verified ON user_management.users(email_verified, phone_verified);

-- Add comments for documentation
COMMENT ON COLUMN user_management.users.name IS 'User display name';
COMMENT ON COLUMN user_management.users.password_reset_token IS 'Token for password reset functionality';
COMMENT ON COLUMN user_management.users.password_reset_expires_at IS 'Expiration time for password reset token';
COMMENT ON COLUMN user_management.users.email_verification_token IS 'Token for email verification';
COMMENT ON COLUMN user_management.users.phone_verification_token IS 'Token for phone verification';
COMMENT ON COLUMN user_management.users.account_status IS 'Current status of the user account';
COMMENT ON COLUMN user_management.users.failed_login_attempts IS 'Number of consecutive failed login attempts';
COMMENT ON COLUMN user_management.users.locked_until IS 'Account locked until this timestamp';
COMMENT ON COLUMN user_management.users.last_activity_at IS 'Last time user was active';
COMMENT ON COLUMN user_management.users.timezone IS 'User preferred timezone';
COMMENT ON COLUMN user_management.users.language_code IS 'User preferred language code';
COMMENT ON COLUMN user_management.users.avatar_url IS 'URL to user avatar image';
COMMENT ON COLUMN user_management.users.bio IS 'User biography/description';
COMMENT ON COLUMN user_management.users.privacy_level IS 'User privacy preference level';
COMMENT ON COLUMN user_management.users.email_notifications IS 'Whether user wants email notifications';
COMMENT ON COLUMN user_management.users.sms_notifications IS 'Whether user wants SMS notifications';
COMMENT ON COLUMN user_management.users.marketing_consent IS 'Whether user consented to marketing communications';
COMMENT ON COLUMN user_management.users.data_processing_consent IS 'Whether user consented to data processing';
COMMENT ON COLUMN user_management.users.consent_given_at IS 'When consent was given';
COMMENT ON COLUMN user_management.users.created_by IS 'Who created this user record';
COMMENT ON COLUMN user_management.users.updated_by IS 'Who last updated this user record';
COMMENT ON COLUMN user_management.users.deleted_at IS 'When user was soft deleted';
COMMENT ON COLUMN user_management.users.version IS 'Version number for optimistic locking';
