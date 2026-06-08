#!/bin/bash
# Deploy the Cost Control panel (API handler + webui page).
# v17-oriented (reads the DeepSeek cache_metrics ledger + idle_model_routing config).
# Restart the container afterward so A0 registers the new API handler.
#
#   CONTAINER=exocortex_v17 bash scripts/install_cost_control.sh
set -e
CONTAINER="${CONTAINER:-exocortex_v17}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

docker cp "$SCRIPT_DIR/patches/api/cost_control.py"      "$CONTAINER:/a0/api/cost_control.py"
docker cp "$SCRIPT_DIR/patches/webui/cost-control.html"  "$CONTAINER:/a0/webui/cost-control.html"
docker exec "$CONTAINER" /opt/venv-a0/bin/python3 -m py_compile /a0/api/cost_control.py

echo "Cost Control deployed to $CONTAINER."
echo "Restart the container to register /api/cost_control, then open /cost-control.html"
