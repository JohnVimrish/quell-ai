# Database Setup for Quell-Ai

This directory contains database migrations, connection management, and user creation scripts for the Quell-Ai application.

## Files Overview

- `connection.py` - Database connection management with connection pooling
- `migrations/` - SQL migration files for database schema setup
- `create_dummy_user.py` - Script to create a test user for development
- `README.md` - This documentation file

## Quick Setup

### 1. Set Environment Variable

Set your PostgreSQL database URL:

**Windows:**
```cmd
set DATABASE_URL=postgresql://username:password@host:port/database
```

**Linux/Mac:**
```bash
export DATABASE_URL=postgresql://username:password@host:port/database
```

### 2. Run Database Setup

**Windows:**
```cmd
setup\setup_database.bat
```

**Linux/Mac:**
```bash
chmod +x setup/setup_database.sh
./setup/setup_database.sh
```

### 3. Test Credentials

After setup, you can login with these test credentials:
- **Email:** `test@quell-ai.com`
- **Password:** `TestPassword123!`

## Manual Setup

If you prefer to run migrations manually:

### 1. Run Migrations in Order

```bash
psql $DATABASE_URL -f code/api/db/migrations/0001_schemas_and_extensions.sql
psql $DATABASE_URL -f code/api/db/migrations/0002_user_management_schema.sql
psql $DATABASE_URL -f code/api/db/migrations/0003_communication_schema.sql
psql $DATABASE_URL -f code/api/db/migrations/0004_ai_intelligence_schema.sql
psql $DATABASE_URL -f code/api/db/migrations/0005_analytics_schema.sql
psql $DATABASE_URL -f code/api/db/migrations/0006_alter_users_table.sql
```

### 2. Create Test User

```bash
python code/api/db/create_dummy_user.py
```

## Database Schema

The application uses multiple schemas for logical separation:

- `user_management` - User accounts, settings, contacts
- `communication` - Calls, messages, conversations
- `ai_intelligence` - AI models, policies, feed items
- `analytics` - Reports, activity logs, metrics
- `system_config` - System configuration

## Security Features

- **Password Hashing:** Uses PBKDF2 with 100,000 iterations
- **Salt Generation:** Cryptographically secure random salts
- **Account Locking:** Failed login attempt tracking
- **Soft Deletes:** Users are marked as deleted, not removed
- **Audit Trail:** Created/updated timestamps and user tracking

## User Management

### User Table Fields

- `id` - Primary key
- `email` - Unique email address
- `password_hash` - Securely hashed password
- `name` - Display name
- `phone_number` - Optional phone number
- `is_active` - Account status
- `email_verified` - Email verification status
- `phone_verified` - Phone verification status
- `account_status` - Account state (active, suspended, etc.)
- `failed_login_attempts` - Security tracking
- `locked_until` - Account lockout timestamp
- `last_login_at` - Last successful login
- `last_activity_at` - Last user activity
- `timezone` - User timezone preference
- `language_code` - User language preference
- `privacy_level` - Privacy settings
- `email_notifications` - Notification preferences
- `sms_notifications` - SMS notification preferences
- `marketing_consent` - Marketing communication consent
- `data_processing_consent` - Data processing consent
- `created_at` - Account creation timestamp
- `updated_at` - Last update timestamp

### User Settings Table

Stores user preferences and configuration:
- AI mode settings
- Spam filtering preferences
- Recording and transcription settings
- Voice cloning preferences
- Forwarding numbers
- Timezone and language settings

## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Check DATABASE_URL format
   - Ensure PostgreSQL is running
   - Verify credentials and permissions

2. **Migration Errors**
   - Check if previous migrations ran successfully
   - Verify database permissions
   - Check for conflicting data

3. **User Creation Failed**
   - Ensure migrations completed successfully
   - Check database connection
   - Verify Python dependencies

### Logs

Check application logs for detailed error information:
- Database connection errors
- Migration failures
- User creation issues
- Authentication problems

## Development

### Adding New Migrations

1. Create new SQL file in `migrations/` directory
2. Use sequential numbering (e.g., `0007_new_feature.sql`)
3. Include rollback instructions in comments
4. Test migration on development database first

### Database Connection

The `DatabaseManager` class provides:
- Connection pooling for performance
- Automatic connection management
- Error handling and logging
- Connection testing utilities

### User Repository

The `UsersRepository` class provides:
- CRUD operations for users
- Password management
- Settings management
- Security features (account locking, etc.)

## Production Considerations

- Use connection pooling for high traffic
- Implement database monitoring
- Set up automated backups
- Monitor failed login attempts
- Implement rate limiting
- Use SSL/TLS for database connections
- Regular security audits
- Monitor for suspicious activity
