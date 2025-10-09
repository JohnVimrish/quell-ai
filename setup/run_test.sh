#!/bin/bash

# Test runner script
echo "🧪 Running Quell AI Tests..."

# Source the environment setup
source "$(dirname "${BASH_SOURCE[0]}")/setup_env.sh"

# Change to the code directory
cd "$PROJECT_ROOT/code"

# Run tests
pytest tests/ -v --tb=short