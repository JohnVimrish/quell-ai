#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

source "$SCRIPT_DIR/setup_env.sh"

start_frontend() {
  echo "🎨 Starting Vite dev server via node-frontend container..."
  docker compose -f "$PROJECT_ROOT/extras/node.yml" up -d
  docker exec node-frontend bash -lc 'cd /app && npm install'
}

start_backend() {
  echo "🧠 Starting Flask backend on http://127.0.0.1:5000"
  cd "$PROJECT_ROOT/backend"
  flask run --reload --port 5000
}

start_frontend &
FRONTEND_PID=$!

trap 'echo "🛑 Shutting down..."; docker compose -f "$PROJECT_ROOT/extras/node.yml" down' EXIT

wait $FRONTEND_PID || true
start_backend