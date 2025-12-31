#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"
BACKEND_DIR="$ROOT_DIR/backend"
VENV_BIN="${VENV_BIN:-$ROOT_DIR/.venv/bin}"
PYTHON_BIN="${PYTHON:-python}"
BACKEND_HOST="${BACKEND_HOST:-0.0.0.0}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_HOST="${FRONTEND_HOST:-0.0.0.0}"
FRONTEND_PORT="${FRONTEND_PORT:-8080}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
  else
    echo "python is required to bootstrap the virtualenv."
    exit 1
  fi
fi

if [ ! -d "$VENV_BIN" ]; then
  echo "Creating local virtualenv at $ROOT_DIR/.venv ..."
  "$PYTHON_BIN" -m venv "$ROOT_DIR/.venv"
fi

# Prefer tools from the local virtualenv if present
if [ -d "$VENV_BIN" ]; then
  export PATH="$VENV_BIN:$PATH"
fi

echo "Installing backend dependencies..."
"$VENV_BIN/python" -m pip install -r "$BACKEND_DIR/requirements.txt"

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required to run the frontend. Install Node.js 18+."
  exit 1
fi

if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
  echo "Installing frontend dependencies..."
  (cd "$FRONTEND_DIR" && npm install)
fi

echo "Checking LLM connectivity (optional for dev; will warn on failure)..."
if ! "$VENV_BIN/python" "$ROOT_DIR/scripts/check_llm_connectivity.py"; then
  echo "Warning: LLM connectivity check failed. Ensure provider API keys are set. Continuing dev startup..."
fi

echo ""
echo "========================================="
echo "BACKEND: Starting FastAPI on http://$BACKEND_HOST:$BACKEND_PORT"
echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================="
(
  cd "$BACKEND_DIR"
  # Run backend with debug logging, prepend all output with [BACKEND]
  uvicorn app.main:app \
    --reload \
    --host "$BACKEND_HOST" \
    --port "$BACKEND_PORT" \
    --log-level debug \
    --access-log \
    --use-colors 2>&1 | sed 's/^/[BACKEND] /'
) &
BACKEND_PID=$!

# Enhanced cleanup function
cleanup() {
  echo ""
  echo "[$(date '+%H:%M:%S')] Shutting down services..."

  # Kill the backend process and all its children
  if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo "Stopping backend (PID: $BACKEND_PID)..."
    pkill -P "$BACKEND_PID" 2>/dev/null || true
    kill "$BACKEND_PID" 2>/dev/null || true
  fi

  # Kill any processes on the backend port as a fallback
  BACKEND_PORT_PIDS=$(lsof -ti:$BACKEND_PORT 2>/dev/null || true)
  if [ -n "$BACKEND_PORT_PIDS" ]; then
    echo "Cleaning up orphaned processes on port $BACKEND_PORT..."
    echo "$BACKEND_PORT_PIDS" | xargs kill -9 2>/dev/null || true
  fi

  # Kill any processes on the frontend port
  FRONTEND_PORT_PIDS=$(lsof -ti:$FRONTEND_PORT 2>/dev/null || true)
  if [ -n "$FRONTEND_PORT_PIDS" ]; then
    echo "Cleaning up processes on port $FRONTEND_PORT..."
    echo "$FRONTEND_PORT_PIDS" | xargs kill -9 2>/dev/null || true
  fi

  echo "✅ Shutdown complete"
}
trap cleanup EXIT INT TERM

# Give backend a moment to start
sleep 2

echo ""
echo "========================================="
echo "FRONTEND: Starting Vite on http://$FRONTEND_HOST:$FRONTEND_PORT"
echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================="
cd "$FRONTEND_DIR"
# Run frontend with debug logging, prepend all output with [FRONTEND]
# This runs in foreground so Ctrl+C will trigger the trap
npm run dev -- --host "$FRONTEND_HOST" --port "$FRONTEND_PORT" --debug --logLevel info 2>&1 | sed 's/^/[FRONTEND] /'
