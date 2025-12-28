#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"
BACKEND_DIR="$ROOT_DIR/backend"
VENV_BIN="${VENV_BIN:-$ROOT_DIR/.venv/bin}"

# Prefer local virtualenv
if [ -d "$VENV_BIN" ]; then
  export PATH="$VENV_BIN:$PATH"
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required for frontend verification. Install Node.js 18+."
  exit 1
fi

if ! command -v python >/dev/null 2>&1; then
  echo "python is required for backend verification."
  exit 1
fi

echo "Verifying frontend build..."
cd "$FRONTEND_DIR"
npm run build

echo "Verifying backend imports..."
cd "$ROOT_DIR"
python -m compileall backend/app

echo "Verification completed successfully."
