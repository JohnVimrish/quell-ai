#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

LOG_DIR="$PROJECT_ROOT/logs/terminal"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/$(date +%Y%m%d).log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "📝 Logging run_dev.sh output to $LOG_FILE"

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

cleanup() {
  echo "🛑 Shutting down development services..."
  docker compose -f "$PROJECT_ROOT/extras/node.yml" down || true
}

trap cleanup EXIT

wait "$FRONTEND_PID" || true
start_backend