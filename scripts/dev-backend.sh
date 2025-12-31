#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR/backend"

if [ ! -d ".venv" ]; then
  python -m venv .venv
fi

source .venv/bin/activate
pip install -r requirements.txt

export PORT="${PORT:-8000}"
uvicorn app.main:app --reload --host 0.0.0.0 --port "$PORT"
