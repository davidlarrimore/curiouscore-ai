#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR/frontend"

echo "========================================="
echo "Starting Frontend Development Server"
echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================="

if [ ! -d "node_modules" ]; then
  echo "[$(date '+%H:%M:%S')] Installing node modules..."
  npm install
fi

export PORT="${PORT:-8080}"
echo "[$(date '+%H:%M:%S')] Starting Vite dev server on port $PORT..."
echo "========================================="

# Run Vite with verbose logging:
# --host 0.0.0.0: Allow external connections
# --debug: Enable debug output
# --logLevel info: Show detailed info logs
npm run dev -- --host 0.0.0.0 --port "$PORT" --debug --logLevel info
