#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "========================================="
echo "Starting CuriousCore with Docker"
echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================="

# Load environment variables if .env exists
if [ -f .env ]; then
  echo "Loading environment from .env file..."
  export $(cat .env | grep -v '^#' | xargs)
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo "❌ Error: Docker is not running. Please start Docker and try again."
  exit 1
fi

# Build and start containers
echo ""
echo "Building and starting containers..."
docker compose up --build

# Note: docker compose up runs in foreground by default
# Press Ctrl+C to stop all services
