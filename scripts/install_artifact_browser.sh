#!/bin/bash
# Install Artifact Browser
# ========================
# Deploys the artifact sidebar integration:
#   - Two Flask API handlers (artifacts_list, artifacts_get)
#   - Sidebar Alpine component (artifacts-store.js, artifacts-list.html)
#   - Patched left-sidebar.html with artifacts section

set -e

CONTAINER="${1:-flamboyant_bell}"
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "[ARTIFACT-BROWSER] Installing to container: $CONTAINER"
echo "[ARTIFACT-BROWSER] Repo root: $REPO_DIR"

py_check() {
    local src="$1" dst="$2"
    if [ ! -f "$src" ]; then
        echo "[ARTIFACT-BROWSER] SKIP (missing): $src"
        return 0
    fi
    docker cp "$src" "$CONTAINER:$dst"
    docker exec "$CONTAINER" sh -c "/opt/venv-a0/bin/python3 -m py_compile '$dst' && echo '[ARTIFACT-BROWSER] OK: $dst'"
}

install_file() {
    local src="$1" dst="$2"
    if [ ! -f "$src" ]; then
        echo "[ARTIFACT-BROWSER] SKIP (missing): $src"
        return 0
    fi
    docker cp "$src" "$CONTAINER:$dst"
    echo "[ARTIFACT-BROWSER] Deployed: $dst"
}

# ── API handlers ────────────────────────────────────────────────────────────
py_check "$REPO_DIR/patches/api/artifacts_list.py" /a0/python/api/artifacts_list.py
py_check "$REPO_DIR/patches/api/artifacts_get.py"  /a0/python/api/artifacts_get.py

# ── Webui sidebar component ─────────────────────────────────────────────────
docker exec "$CONTAINER" sh -c "mkdir -p /a0/webui/components/sidebar/artifacts"

install_file "$REPO_DIR/patches/webui/components/sidebar/artifacts/artifacts-store.js" \
    /a0/webui/components/sidebar/artifacts/artifacts-store.js

install_file "$REPO_DIR/patches/webui/components/sidebar/artifacts/artifacts-list.html" \
    /a0/webui/components/sidebar/artifacts/artifacts-list.html

# ── Patched left-sidebar ────────────────────────────────────────────────────
install_file "$REPO_DIR/patches/webui/left-sidebar.html" \
    /a0/webui/components/sidebar/left-sidebar.html

# ── Patched sidebar-store (adds 'artifacts' section state) ──────────────────
install_file "$REPO_DIR/patches/webui/components/sidebar/sidebar-store.js" \
    /a0/webui/components/sidebar/sidebar-store.js

# ── Ensure artifacts dir exists ─────────────────────────────────────────────
docker exec "$CONTAINER" sh -c "mkdir -p /a0/usr/workdir/artifacts"

# ── Artifact index (gallery page with postMessage navigation) ───────────────
install_file "$REPO_DIR/patches/artifacts/index.html" \
    /a0/usr/workdir/artifacts/index.html

# ── Clear API pycache ───────────────────────────────────────────────────────
docker exec "$CONTAINER" sh -c "
    rm -f /a0/python/api/__pycache__/artifacts_list.cpython-312.pyc \
          /a0/python/api/__pycache__/artifacts_get.cpython-312.pyc 2>/dev/null || true
"

echo ""
echo "[ARTIFACT-BROWSER] Done. Reload the Agent Zero UI to activate."
echo "[ARTIFACT-BROWSER] Routes: GET /artifacts_list  POST /artifacts_get"
echo "[ARTIFACT-BROWSER] Sidebar: Artifacts section added below Tasks"
