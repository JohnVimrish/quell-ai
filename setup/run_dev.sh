#!/bin/bash

# Development runner script
echo "🚀 Starting Quell AI Development Server..."

# Source the environment setup
source "$(dirname "${BASH_SOURCE[0]}")/setup_env.sh"

# Change to the code directory
cd "$PROJECT_ROOT/code"

# Start the development server with auto-reload
echo "🌐 Starting server at http://localhost:8080"
"$PROJECT_ROOT/pvenv/Scripts/python" api/run.py