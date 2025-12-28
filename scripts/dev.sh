#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"
BACKEND_DIR="$ROOT_DIR/backend"
VENV_BIN="${VENV_BIN:-$ROOT_DIR/.venv/bin}"

# Prefer tools from the local virtualenv if present
if [ -d "$VENV_BIN" ]; then
  export PATH="$VENV_BIN:$PATH"
fi

if ! command -v uvicorn >/dev/null 2>&1; then
  echo "uvicorn is not installed. Activate your venv or install backend deps with:"
  echo "  python -m venv .venv && source .venv/bin/activate && pip install -r backend/requirements.txt"
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required to run the frontend. Install Node.js 18+."
  exit 1
fi

echo "Starting FastAPI backend on http://localhost:8000 ..."
(
  cd "$BACKEND_DIR"
  uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
) &
BACKEND_PID=$!

cleanup() {
  if kill -0 "$BACKEND_PID" >/dev/null 2>&1; then
    kill "$BACKEND_PID"
  fi
}
trap cleanup EXIT

echo "Starting Vite frontend on http://localhost:8080 ..."
cd "$FRONTEND_DIR"
npm run dev -- --host 0.0.0.0 --port 8080
