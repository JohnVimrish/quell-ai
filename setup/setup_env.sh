#!/bin/bash

# Quell AI Environment Setup Script
echo "🚀 Setting up Quell AI environment..."

# Get the absolute path of the project directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "📁 Project root: $PROJECT_ROOT"


# Add project root and code directory to Python path only if not already set
# Add project root and code directory to Python path only if not already present
add_to_pythonpath() {
    case ":$PYTHONPATH:" in
        *":$1:"*) :;; # already there
        *) PYTHONPATH="$1${PYTHONPATH:+:$PYTHONPATH}";;
    esac
}

add_to_pythonpath "$PROJECT_ROOT/code"
export PYTHONPATH
echo "🔧 PYTHONPATH set to: $PYTHONPATH"


# Core application settings
export FLASK_ENV=development
export FLASK_APP=api.app:create_app
export PORT=8080
export DEBUG=true

# # Database configuration
# Replace with your actual Neon DB connection string
export DATABASE_URL='postgresql://user_ai:Abc$12345@localhost:15433/quell_ai'

# # AI/ML Model configuration
export EMBED_MODEL="sentence-transformers/all-MiniLM-L6-v2"

# Logging configuration
export LOG_LEVEL=DEBUG
export SERVICE_NAME=quell-ai

# Optional: Graylog configuration (uncomment if using)
export GRAYLOG_HOST=localhost
export GRAYLOG_PORT=12201

# Provider API Keys (uncomment and set as needed)
# export TWILIO_ACCOUNT_SID=your_twilio_account_sid
# export TWILIO_AUTH_TOKEN=your_twilio_auth_token
# export TWILIO_PHONE_NUMBER=your_twilio_phone_number

# export DEEPGRAM_API_KEY=your_deepgram_api_key

# export ELEVENLABS_API_KEY=your_elevenlabs_api_key

# OpenAI or other AI provider keys
# export OPENAI_API_KEY=your_openai_api_key

# Security settings
export SECRET_KEY=$(openssl rand -base64 32)
export JWT_SECRET_KEY=$(openssl rand -base64 32)

# Application configuration file path
export APP_CONFIG_FILE="$PROJECT_ROOT/config/app.json"

# Activate virtual environment if it exists
if [ -d "$PROJECT_ROOT/pvenv" ]; then
    echo "🔧 Activating virtual environment..."
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
        # Windows (Git Bash, Cygwin, etc.)
        source "$PROJECT_ROOT/pvenv/Scripts/activate"
    else
        # Linux/macOS
        source "$PROJECT_ROOT/pvenv/bin/activate"
    fi
else
    echo "⚠️  No virtual environment found. Consider creating one with: python -m venv pvenv"
fi

# Verify Python can find the modules
echo "🔍 Verifying Python path..."
python -c "import sys; print('Python paths:'); [print(f'  {p}') for p in sys.path if 'ai-call-copilot' in p or p == '']" 2>/dev/null || echo "⚠️  Python verification failed"

echo "✅ Environment setup complete!"
echo ""
echo "🎯 Quick commands:"
echo "  Start development server: uvicorn api.app:create_app --host 0.0.0.0 --port 8080 --reload"
echo "  Run tests: pytest"
echo "  Check health: curl http://localhost:8080/healthz"
echo ""
echo "📝 Don't forget to:"
echo "  1. Update DATABASE_URL with your actual database connection"
echo "  2. Set your API keys for external services"
echo "  3. Update SECRET_KEY for production use"