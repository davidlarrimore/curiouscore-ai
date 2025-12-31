#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

SERVICE="${1:-}"

if [ -z "$SERVICE" ]; then
  echo "========================================="
  echo "Viewing logs for ALL services"
  echo "Press Ctrl+C to exit"
  echo "========================================="
  docker compose logs -f --tail=100
elif [ "$SERVICE" = "backend" ] || [ "$SERVICE" = "frontend" ]; then
  echo "========================================="
  echo "Viewing logs for $SERVICE"
  echo "Press Ctrl+C to exit"
  echo "========================================="
  docker compose logs -f --tail=100 "$SERVICE"
else
  echo "Usage: $0 [backend|frontend]"
  echo ""
  echo "Examples:"
  echo "  $0              # View all logs"
  echo "  $0 backend      # View backend logs only"
  echo "  $0 frontend     # View frontend logs only"
  exit 1
fi
