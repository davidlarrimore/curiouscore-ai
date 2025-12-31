#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "========================================="
echo "Reset PostgreSQL Database"
echo "========================================="
echo ""
echo "⚠️  WARNING: This will DELETE all data in the database!"
echo ""
read -p "Are you sure you want to continue? (type 'yes' to confirm): " confirm

if [ "$confirm" != "yes" ]; then
  echo "Aborted."
  exit 0
fi

echo ""
echo "Stopping containers..."
docker compose down

echo ""
echo "Removing PostgreSQL volume..."
docker volume rm curiouscore-ai_postgres-data 2>/dev/null || echo "Volume already removed"

echo ""
echo "Starting containers with fresh database..."
docker compose up -d

echo ""
echo "✅ Database has been reset!"
echo ""
echo "View logs with: ./scripts/docker-logs.sh backend"
