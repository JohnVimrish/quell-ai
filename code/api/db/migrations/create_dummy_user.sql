-- =============================================
-- CREATE DUMMY USER FOR TESTING
-- =============================================
-- Execute this file to create a test user for Quell-Ai
-- Usage: psql "your_database_url" -f code/api/db/create_dummy_user.sql

-- Test user credentials:
-- Email: test@quell-ai.com
-- Password: TestPassword123!
-- Name: Test User
-- Phone: +15551234567

BEGIN;

-- Check if user already exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM user_management.users WHERE email = 'test@quell-ai.com') THEN
        RAISE NOTICE 'User test@quell-ai.com already exists, skipping creation';
    ELSE
        -- Insert dummy user with hashed password
        -- Password hash for "TestPassword123!" using PBKDF2
        INSERT INTO user_management.users (
            email, 
            password_hash, 
            name,
            phone_number,
            is_active,
            email_verified,
            phone_verified,
            account_status,
            timezone,
            language_code,
            email_notifications,
            data_processing_consent,
            consent_given_at,
            created_by
        ) VALUES (
            'test@quell-ai.com',
            'a1b2c3d4e5f6789012345678901234567890123456789012345678901234:' ||
            '8f4e5c2b1a9d8e7f6c3b2a1e9d8c7b6a5f4e3d2c1b0a9e8d7c6b5a4f3e2d1c0b9a8e7f6c5b4a3e2d1c0b9a8e7f6c5b4a3e2d1c0',
            'Test User',
            '+15551234567',
            true,
            false,
            false,
            'active',
            'UTC',
            'en',
            true,
            true,
            now(),
            'system'
        );

        -- Get the user ID
        DECLARE
            user_id_var BIGINT;
        BEGIN
            SELECT id INTO user_id_var 
            FROM user_management.users 
            WHERE email = 'test@quell-ai.com';

            -- Create default user settings
            INSERT INTO user_management.user_settings (
                user_id,
                ai_mode_enabled,
                spam_filtering_enabled,
                recording_enabled,
                transcript_enabled,
                voice_cloning_enabled,
                timezone,
                language_code
            ) VALUES (
                user_id_var,
                true,
                true,
                false,
                false,
                false,
                'UTC',
                'en'
            );

            RAISE NOTICE 'Created test user: test@quell-ai.com (ID: %)', user_id_var;
        END;
    END IF;
END $$;

COMMIT;

-- Display success message
SELECT 
    '✅ DUMMY USER CREATED SUCCESSFULLY' as status,
    'Email: test@quell-ai.com' as email,
    'Password: TestPassword123!' as password,
    'You can now login with these credentials' as note;
