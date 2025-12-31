#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR/backend"

echo "========================================="
echo "Starting Backend Development Server"
echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================="

if [ ! -d ".venv" ]; then
  echo "[$(date '+%H:%M:%S')] Creating virtual environment..."
  python -m venv .venv
fi

source .venv/bin/activate
echo "[$(date '+%H:%M:%S')] Installing/updating dependencies..."
pip install -r requirements.txt

export PORT="${PORT:-8000}"
echo "[$(date '+%H:%M:%S')] Starting uvicorn on port $PORT with DEBUG logging..."
echo "========================================="

# Run uvicorn with maximum verbosity:
# --log-level debug: Enable debug-level logging
# --access-log: Show all HTTP requests
# --reload: Auto-reload on file changes
# --use-colors: Colorize output for better readability
uvicorn app.main:app \
  --reload \
  --host 0.0.0.0 \
  --port "$PORT" \
  --log-level debug \
  --access-log \
  --use-colors
