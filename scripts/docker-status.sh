#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "========================================="
echo "CuriousCore Docker Status"
echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================="
echo ""

# Show container status
echo "Container Status:"
docker compose ps

echo ""
echo "========================================="
echo ""

# Show resource usage
echo "Resource Usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" \
  $(docker compose ps -q 2>/dev/null) 2>/dev/null || echo "No running containers"

echo ""
echo "========================================="
echo ""
echo "Quick Commands:"
echo "  View logs:        ./scripts/docker-logs.sh [backend|frontend]"
echo "  Restart:          docker compose restart [backend|frontend]"
echo "  Rebuild:          docker compose up --build -d"
echo "  Shell access:     docker compose exec backend bash"
echo "                    docker compose exec frontend sh"
