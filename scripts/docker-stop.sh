#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "========================================="
echo "Stopping CuriousCore Docker services"
echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================="

docker compose down

echo ""
echo "✅ All containers stopped"
echo ""
echo "To remove volumes as well (reset database), run:"
echo "  docker compose down -v"
