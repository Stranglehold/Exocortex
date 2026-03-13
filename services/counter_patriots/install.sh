#!/usr/bin/env bash
# install.sh — Deploy Counter-Patriots standalone service
# Part of the Exocortex services/ layer.
#
# Usage:
#   ./install.sh             # start with defaults
#   ./install.sh --stop      # stop and remove containers
#   ./install.sh --rebuild   # force image rebuild

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Defaults — override with env vars
export CP_DB_PASSWORD="${CP_DB_PASSWORD:-cp_dev_password}"
export CP_ANALYST_TOKEN="${CP_ANALYST_TOKEN:-dev_analyst_token}"
export CP_LLM_URL="${CP_LLM_URL:-http://host.docker.internal:1234/v1}"
export CP_LLM_MODEL="${CP_LLM_MODEL:-qwen2.5-14b-instruct}"
export CP_EMBEDDING_MODEL="${CP_EMBEDDING_MODEL:-all-MiniLM-L6-v2}"
export CP_INGEST_INTERVAL_MINUTES="${CP_INGEST_INTERVAL_MINUTES:-30}"

if [[ "$1" == "--stop" ]]; then
    echo "[cp] Stopping Counter-Patriots..."
    docker compose down
    echo "[cp] Stopped."
    exit 0
fi

if [[ "$1" == "--migrate" ]]; then
    echo "[cp] Running CDS v2 Phase 1 migration..."
    echo "[cp] Waiting for PostgreSQL to be ready..."
    for i in $(seq 1 30); do
        if docker exec cp_postgres pg_isready -U cp_user -d counter_patriots > /dev/null 2>&1; then
            break
        fi
        sleep 2
    done
    docker exec -i cp_postgres psql -U cp_user -d counter_patriots \
        < "$SCRIPT_DIR/migrations/001_cds_v2_founding.sql"
    echo "[cp] Migration complete."
    echo "[cp] Update CP_DB_URL in docker-compose.yml to use cds_app for the app service."
    exit 0
fi

if [[ "$1" == "--rebuild" ]]; then
    echo "[cp] Rebuilding Counter-Patriots image..."
    docker compose build --no-cache
fi

echo "[cp] Starting Counter-Patriots..."
echo "[cp]   LLM: $CP_LLM_URL ($CP_LLM_MODEL)"
echo "[cp]   Port: 7731"
echo "[cp]   Ingest interval: ${CP_INGEST_INTERVAL_MINUTES}m"

docker compose up -d

echo "[cp] Waiting for PostgreSQL to be ready..."
for i in $(seq 1 30); do
    if docker exec cp_postgres pg_isready -U cp_user -d counter_patriots > /dev/null 2>&1; then
        echo "[cp] PostgreSQL ready."
        break
    fi
    sleep 2
done

echo "[cp] Waiting for app to be ready..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:7731/api/health > /dev/null 2>&1; then
        echo "[cp] Counter-Patriots is operational."
        break
    fi
    sleep 2
done

echo ""
echo "[cp] Endpoints:"
echo "  GET  http://localhost:7731/api/health"
echo "  POST http://localhost:7731/api/drift"
echo "  POST http://localhost:7731/api/silence"
echo "  POST http://localhost:7731/api/activation"
echo "  POST http://localhost:7731/api/record"
echo "  GET  http://localhost:7731/api/network"
echo "  POST http://localhost:7731/api/contradictions   (analyst auth required)"
echo "  POST http://localhost:7731/api/staging           (analyst auth required)"
echo "  POST http://localhost:7731/admin/promote_claim   (analyst auth required)"
echo "  POST http://localhost:7731/admin/return_to_staged (analyst auth required)"
echo "  POST http://localhost:7731/admin/register_edge   (analyst auth required)"
echo "  POST http://localhost:7731/admin/ingest          (analyst auth required)"
echo ""
echo "[cp] Analyst token: $CP_ANALYST_TOKEN"
echo "[cp] To tail logs: docker logs -f cp_app"
echo "[cp] To run migration (existing deploy): ./install.sh --migrate"
