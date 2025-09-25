#!/bin/bash

# Database Setup Script for Quell-Ai
# This script sets up the database with migrations and creates a dummy user

set -e  # Exit on any error

echo "🚀 Setting up Quell-Ai Database..."

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ Error: DATABASE_URL environment variable is not set"
    echo "Please set your PostgreSQL connection string:"
    echo "export DATABASE_URL='postgresql://username:password@host:port/database'"
    exit 1
fi

# Check if psql is available
if ! command -v psql &> /dev/null; then
    echo "❌ Error: psql command not found"
    echo "Please install PostgreSQL client tools"
    exit 1
fi

echo "📋 Running database migrations..."

# Run migrations in order
MIGRATIONS_DIR="code/api/db/migrations"

# Check if migrations directory exists
if [ ! -d "$MIGRATIONS_DIR" ]; then
    echo "❌ Error: Migrations directory not found: $MIGRATIONS_DIR"
    exit 1
fi

# Run each migration file
for migration in $(ls $MIGRATIONS_DIR/*.sql | sort); do
    echo "Running migration: $(basename $migration)"
    psql "$DATABASE_URL" -f "$migration"
    if [ $? -eq 0 ]; then
        echo "✅ Migration $(basename $migration) completed successfully"
    else
        echo "❌ Migration $(basename $migration) failed"
        exit 1
    fi
done

echo "🎯 Creating dummy user for testing..."

# Run the dummy user creation script
python3 code/api/db/create_dummy_user.py

if [ $? -eq 0 ]; then
    echo "✅ Database setup completed successfully!"
    echo ""
    echo "🔐 Test Credentials:"
    echo "Email: test@quell-ai.com"
    echo "Password: TestPassword123!"
    echo ""
    echo "You can now start your application and login with these credentials."
else
    echo "❌ Failed to create dummy user"
    exit 1
fi
