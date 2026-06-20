#!/usr/bin/env bash
# Deploy the Exocortex SearXNG override settings (academic engines routed into the
# general category so the agent's search_engine tool gets arXiv/scholar/pubmed/
# crossref/openalex results on every search). Idempotent. Run from host or in-container.
set -e
CONTAINER_NAME="${CONTAINER_NAME:-exocortex_v16}"
SRC="$(dirname "$0")/settings.yml"
DEST="/etc/searxng/settings.yml"
_exec() { MSYS_NO_PATHCONV=1 docker exec "$@"; }
if command -v docker &>/dev/null && docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    _exec "${CONTAINER_NAME}" cp "${DEST}" "${DEST}.bak.$(date +%s)" 2>/dev/null || true
    docker cp "${SRC}" "${CONTAINER_NAME}:${DEST}"
    _exec "${CONTAINER_NAME}" sh -lc "supervisorctl restart searxng 2>/dev/null || kill \$(pgrep -f searx/webapp.py) 2>/dev/null || true"
else
    cp "${DEST}" "${DEST}.bak.$(date +%s)" 2>/dev/null || true
    cp "${SRC}" "${DEST}"
    supervisorctl restart searxng 2>/dev/null || kill $(pgrep -f searx/webapp.py) 2>/dev/null || true
fi
echo "  SearXNG override deployed + restarted."
