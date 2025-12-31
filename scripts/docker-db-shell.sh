#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "========================================="
echo "Connecting to PostgreSQL Database"
echo "========================================="

# Check if postgres container is running
if ! docker compose ps postgres | grep -q "Up"; then
  echo "❌ PostgreSQL container is not running"
  echo "Start it with: ./scripts/docker-dev.sh"
  exit 1
fi

# Get database credentials from .env or use defaults
POSTGRES_USER="${POSTGRES_USER:-curiouscore}"
POSTGRES_DB="${POSTGRES_DB:-curiouscore}"

echo "Connecting to database: $POSTGRES_DB as user: $POSTGRES_USER"
echo ""

docker compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
