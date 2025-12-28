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

echo "Starting FastAPI backend on http://$BACKEND_HOST:$BACKEND_PORT ..."
(
  cd "$BACKEND_DIR"
  uvicorn app.main:app --reload --host "$BACKEND_HOST" --port "$BACKEND_PORT"
) &
BACKEND_PID=$!

cleanup() {
  if kill -0 "$BACKEND_PID" >/dev/null 2>&1; then
    kill "$BACKEND_PID"
  fi
}
trap cleanup EXIT

echo "Starting Vite frontend on http://$FRONTEND_HOST:$FRONTEND_PORT ..."
cd "$FRONTEND_DIR"
npm run dev -- --host "$FRONTEND_HOST" --port "$FRONTEND_PORT"
