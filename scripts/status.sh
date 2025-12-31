#!/usr/bin/env bash

echo "========================================="
echo "CuriousCore Service Status"
echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================="

# Check backend
BACKEND_PIDS=$(lsof -ti:8000 2>/dev/null || true)
if [ -n "$BACKEND_PIDS" ]; then
  echo "✅ Backend running on port 8000 (PIDs: $BACKEND_PIDS)"
  ps -p $BACKEND_PIDS -o pid,ppid,command
else
  echo "❌ Backend not running on port 8000"
fi

echo ""

# Check frontend
FRONTEND_PIDS=$(lsof -ti:8080 2>/dev/null || true)
if [ -n "$FRONTEND_PIDS" ]; then
  echo "✅ Frontend running on port 8080 (PIDs: $FRONTEND_PIDS)"
  ps -p $FRONTEND_PIDS -o pid,ppid,command
else
  echo "❌ Frontend not running on port 8080"
fi

echo ""
echo "========================================="
