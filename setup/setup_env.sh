#!/bin/bash

# Quell AI Environment Setup Script
echo "🚀 Setting up Quell AI environment..."

# Resolve project root and export for later scripts
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PROJECT_ROOT
echo "📁 Project root: $PROJECT_ROOT"

# Helper to append unique paths to PYTHONPATH
add_to_pythonpath() {
    case ":$PYTHONPATH:" in
        *":$1:") ;;
        *) PYTHONPATH="$1${PYTHONPATH:+:$PYTHONPATH}" ;;
    esac
}

# Ensure backend package is importable
add_to_pythonpath "$PROJECT_ROOT/backend"
export PYTHONPATH
echo "🔧 PYTHONPATH set to: $PYTHONPATH"

# Core application settings
export FLASK_ENV=${FLASK_ENV:-development}
export FLASK_APP=${FLASK_APP:-api.app:create_app}
export PORT=${PORT:-5000}
export DEBUG=${DEBUG:-true}
export FRONTEND_DEV_URL=${FRONTEND_DEV_URL:-http://localhost:5173}

# Database configuration (override in .env as needed)
export DATABASE_URL=${DATABASE_URL:-'postgresql+psycopg://user_ai:Abc$12345@localhost:15433/quell_ai'}

# AI/ML Model configuration
export OPENAI_CHAT_MODEL=${OPENAI_CHAT_MODEL:-"gpt-4o-mini"}
export OPENAI_EMBED_MODEL=${OPENAI_EMBED_MODEL:-"text-embedding-3-small"}
export OPENAI_EMBED_DIM=${OPENAI_EMBED_DIM:-1536}

# Logging configuration
export LOG_LEVEL=${LOG_LEVEL:-DEBUG}
export SERVICE_NAME=${SERVICE_NAME:-quell-ai}

# Optional: Graylog configuration (uncomment if using)
export GRAYLOG_HOST=${GRAYLOG_HOST:-localhost}
export GRAYLOG_PORT=${GRAYLOG_PORT:-12201}

# Provider API Keys (uncomment and set as needed)
# export TWILIO_ACCOUNT_SID=your_twilio_account_sid
# export TWILIO_AUTH_TOKEN=your_twilio_auth_token
# export TWILIO_PHONE_NUMBER=your_twilio_phone_number
# export DEEPGRAM_API_KEY=your_deepgram_api_key
# export ELEVENLABS_API_KEY=your_elevenlabs_api_key
# export OPENAI_API_KEY=your_openai_api_key

# Security settings (only use random secrets for local dev)
export SECRET_KEY=${SECRET_KEY:-$(openssl rand -base64 32)}
export JWT_SECRET_KEY=${JWT_SECRET_KEY:-$(openssl rand -base64 32)}

# Application configuration file path
export APP_CONFIG_FILE="$PROJECT_ROOT/backend/config/app.json"

# Activate virtual environment if it exists
if [ -d "$PROJECT_ROOT/pvenv" ]; then
    echo "🔧 Activating virtual environment..."
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
        source "$PROJECT_ROOT/pvenv/Scripts/activate"
    else
        source "$PROJECT_ROOT/pvenv/bin/activate"
    fi
else
    echo "⚠️  No virtual environment found. Consider creating one with: python -m venv pvenv"
fi

# Verify Python can find backend packages
echo "🔍 Verifying Python path..."
python -c "import sys; print('Python paths:'); [print(f'  {p}') for p in sys.path if 'ai-call-copilot' in p or p == '']" 2>/dev/null || echo "⚠️  Python verification failed"

echo "✅ Environment setup complete!"
echo ""
echo "🎯 Quick commands:"
echo "  Start backend: flask --app api.app:create_app run --reload"
echo "  Frontend dev server: docker compose -f extras/node.yml up"
echo "  Run tests: cd backend && pytest"
echo "  Check health: curl http://localhost:$PORT/api/status"
echo ""
echo "📝 Don't forget to update environment variables for your local credentials and API keys."
