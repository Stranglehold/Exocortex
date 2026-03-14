#!/usr/bin/env bash
# install.sh — Deploy OSS standalone service
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
export OSS_DB_PASSWORD="${OSS_DB_PASSWORD:-oss_admin_dev_password}"
export OSS_ANALYST_TOKEN="${OSS_ANALYST_TOKEN:-dev_analyst_token}"
export OSS_LLM_URL="${OSS_LLM_URL:-http://host.docker.internal:1234/v1}"
export OSS_LLM_MODEL="${OSS_LLM_MODEL:-qwen2.5-14b-instruct}"
export OSS_EMBEDDING_MODEL="${OSS_EMBEDDING_MODEL:-all-MiniLM-L6-v2}"
export OSS_INGEST_INTERVAL_MINUTES="${OSS_INGEST_INTERVAL_MINUTES:-30}"

if [[ "$1" == "--stop" ]]; then
    echo "[oss] Stopping OSS..."
    docker compose down
    echo "[oss] Stopped."
    exit 0
fi

if [[ "$1" == "--migrate" ]]; then
    echo "[oss] Running CDS v2 Phase 1 migration..."
    echo "[oss] Waiting for PostgreSQL to be ready..."
    for i in $(seq 1 30); do
        if docker exec oss_postgres pg_isready -U oss_admin -d oss > /dev/null 2>&1; then
            break
        fi
        sleep 2
    done
    docker exec -i oss_postgres psql -U oss_admin -d oss \
        < "$SCRIPT_DIR/migrations/001_cds_v2_founding.sql"
    echo "[oss] Migration complete."
    echo "[oss] Update OSS_DB_URL in docker-compose.yml to use oss_app for the app service."
    exit 0
fi

if [[ "$1" == "--rebuild" ]]; then
    echo "[oss] Rebuilding OSS image..."
    docker compose build --no-cache
fi

echo "[oss] Starting OSS..."
echo "[oss]   LLM: $OSS_LLM_URL ($OSS_LLM_MODEL)"
echo "[oss]   Port: 7731"
echo "[oss]   Ingest interval: ${OSS_INGEST_INTERVAL_MINUTES}m"

docker compose up -d

echo "[oss] Waiting for PostgreSQL to be ready..."
for i in $(seq 1 30); do
    if docker exec oss_postgres pg_isready -U oss_admin -d oss > /dev/null 2>&1; then
        echo "[oss] PostgreSQL ready."
        break
    fi
    sleep 2
done

echo "[oss] Waiting for app to be ready..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:7731/api/health > /dev/null 2>&1; then
        echo "[oss] OSS is operational."
        break
    fi
    sleep 2
done

echo ""
echo "[oss] Endpoints:"
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
echo "  POST http://localhost:7731/admin/submit_claim   (analyst auth required)"
echo ""
echo "[oss] Analyst token: $OSS_ANALYST_TOKEN"
echo "[oss] To tail logs: docker logs -f oss_app"
echo "[oss] To run migration (existing deploy): ./install.sh --migrate"
