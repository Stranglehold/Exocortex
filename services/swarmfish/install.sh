#!/bin/bash
# install.sh — SWARMFISH service deployment
#
# Usage:
#   ./install.sh           — first-time install (build + start)
#   ./install.sh --restart — rebuild app container, restart service
#   ./install.sh --stop    — stop all containers
#   ./install.sh --logs    — tail service logs
#
# Ports: Postgres 5435, Redis 6380, SWARMFISH app 7732
# Separate from OSS service (Postgres 5433, app 7731) — isolated by design.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

case "${1:-}" in
  --stop)
    echo "[SWARMFISH] Stopping containers..."
    docker compose down
    exit 0
    ;;

  --logs)
    docker compose logs -f swarmfish
    exit 0
    ;;

  --restart)
    echo "[SWARMFISH] Rebuilding app container..."
    docker compose build swarmfish
    docker compose up -d swarmfish
    echo "[SWARMFISH] Restarted. Logs: ./install.sh --logs"
    exit 0
    ;;
esac

# ── First-time install ──────────────────────────────────────────────────

echo "[SWARMFISH] Building and starting services..."
docker compose build
docker compose up -d

echo "[SWARMFISH] Waiting for Postgres to be ready..."
for i in $(seq 1 15); do
    if docker compose exec -T postgres pg_isready -U swarmfish_admin -d swarmfish > /dev/null 2>&1; then
        echo "[SWARMFISH] Postgres ready."
        break
    fi
    echo "[SWARMFISH] Waiting... ($i/15)"
    sleep 2
done

echo "[SWARMFISH] Verifying app health..."
sleep 3
for i in $(seq 1 10); do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "X-Analyst-Token: dev_analyst_token" \
        http://localhost:7732/health 2>/dev/null || echo "000")
    if [ "$STATUS" = "200" ]; then
        echo "[SWARMFISH] Health check passed."
        break
    fi
    echo "[SWARMFISH] App not ready yet (HTTP $STATUS), waiting... ($i/10)"
    sleep 3
done

echo ""
echo "[SWARMFISH] ✓ Deployment complete."
echo ""
echo "  Service:  http://localhost:7732"
echo "  Postgres: localhost:5435 (db=swarmfish, user=swarmfish_admin)"
echo "  Redis:    localhost:6380"
echo ""
echo "  Test predict:"
echo "    curl -s -X POST http://localhost:7732/acp/predict \\"
echo "      -H 'X-Analyst-Token: dev_analyst_token' \\"
echo "      -H 'Content-Type: application/json' \\"
echo "      -d '{\"question\": \"Will Brent crude exceed 90 USD in the next 3 weeks?\", \"domain\": \"commodities\"}'"
echo ""
echo "  Profile list:"
echo "    curl -s http://localhost:7732/acp/profiles -H 'X-Analyst-Token: dev_analyst_token'"
