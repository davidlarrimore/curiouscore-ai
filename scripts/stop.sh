#!/usr/bin/env bash
set -euo pipefail

echo "========================================="
echo "Stopping CuriousCore Services"
echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================="

# Kill backend on port 8000
BACKEND_PIDS=$(lsof -ti:8000 2>/dev/null || true)
if [ -n "$BACKEND_PIDS" ]; then
  echo "Stopping backend processes on port 8000..."
  echo "$BACKEND_PIDS" | xargs kill -9
  echo "✅ Backend stopped"
else
  echo "ℹ️  No backend process running on port 8000"
fi

# Kill frontend on port 8080
FRONTEND_PIDS=$(lsof -ti:8080 2>/dev/null || true)
if [ -n "$FRONTEND_PIDS" ]; then
  echo "Stopping frontend processes on port 8080..."
  echo "$FRONTEND_PIDS" | xargs kill -9
  echo "✅ Frontend stopped"
else
  echo "ℹ️  No frontend process running on port 8080"
fi

# Also kill any orphaned uvicorn processes
UVICORN_PIDS=$(pgrep -f "uvicorn app.main:app" 2>/dev/null || true)
if [ -n "$UVICORN_PIDS" ]; then
  echo "Stopping orphaned uvicorn processes..."
  echo "$UVICORN_PIDS" | xargs kill -9
  echo "✅ Uvicorn processes stopped"
fi

# Kill any orphaned vite processes
VITE_PIDS=$(pgrep -f "vite.*dev" 2>/dev/null || true)
if [ -n "$VITE_PIDS" ]; then
  echo "Stopping orphaned vite processes..."
  echo "$VITE_PIDS" | xargs kill -9
  echo "✅ Vite processes stopped"
fi

echo "========================================="
echo "All services stopped"
echo "========================================="
