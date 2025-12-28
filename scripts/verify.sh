#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"
BACKEND_DIR="$ROOT_DIR/backend"
VENV_BIN="${VENV_BIN:-$ROOT_DIR/.venv/bin}"
PYTHON_BIN="${PYTHON:-python}"

# Prefer local virtualenv
if [ -d "$VENV_BIN" ]; then
  export PATH="$VENV_BIN:$PATH"
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required for frontend verification. Install Node.js 18+."
  exit 1
fi

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
  else
    echo "python is required for backend verification."
    exit 1
  fi
fi

if [ ! -x "$FRONTEND_DIR/node_modules/.bin/vite" ]; then
  echo "Installing frontend dependencies (vite missing)..."
  cd "$FRONTEND_DIR"
  npm install
  cd "$ROOT_DIR"
fi

echo "Verifying frontend build..."
cd "$FRONTEND_DIR"
npm run build

echo "Verifying backend imports..."
cd "$ROOT_DIR"
"$PYTHON_BIN" -m compileall backend/app

echo "Checking LLM connectivity (requires provider API keys)..."
if ! "$PYTHON_BIN" scripts/check_llm_connectivity.py; then
  echo "LLM connectivity check failed."
  exit 1
fi

echo "Running backend LLM connectivity tests..."
"$PYTHON_BIN" -m unittest backend.tests.test_llm_connectivity

echo "Verification completed successfully."
