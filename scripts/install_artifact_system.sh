#!/usr/bin/env bash
# Install Artifact Authoring System (Phase 1)
# Deploys: artifact_create tool, templates, themes, manifest
#
# Usage:
#   ./scripts/install_artifact_system.sh
#   CONTAINER=my_container ./scripts/install_artifact_system.sh

set -e

CONTAINER="${CONTAINER:-exocortex_v16}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

# Source paths
TOOL_SRC="$REPO_DIR/tools/artifact_create.py"
TEMPLATES_SRC="$REPO_DIR/artifact_templates"

# Container paths
TOOL_DEST="/a0/usr/plugins/exocortex/tools/artifact_create.py"
TEMPLATES_DEST="/a0/usr/artifact_templates"
OUTPUT_DEST="/a0/work/artifacts"

echo "[ARTIFACT-INSTALL] Deploying Artifact Authoring System to $CONTAINER..."
echo ""

# ── Tool ─────────────────────────────────────────────────────────────────────
echo "[ARTIFACT-INSTALL] Installing artifact_create tool..."
docker cp "$TOOL_SRC" "$CONTAINER:$TOOL_DEST"

# ── Directories ───────────────────────────────────────────────────────────────
echo "[ARTIFACT-INSTALL] Creating template directories..."
docker exec "$CONTAINER" sh -c "mkdir -p '$TEMPLATES_DEST/themes' '$OUTPUT_DEST'"

# ── Themes ────────────────────────────────────────────────────────────────────
echo "[ARTIFACT-INSTALL] Copying themes..."
for theme_file in "$TEMPLATES_SRC/themes/"*.json; do
    [ -f "$theme_file" ] || continue
    name="$(basename "$theme_file")"
    docker cp "$theme_file" "$CONTAINER:$TEMPLATES_DEST/themes/$name"
    echo "  theme: $name"
done

# ── Manifest ──────────────────────────────────────────────────────────────────
echo "[ARTIFACT-INSTALL] Copying manifest..."
docker cp "$TEMPLATES_SRC/manifest.json" "$CONTAINER:$TEMPLATES_DEST/manifest.json"

# ── Templates ─────────────────────────────────────────────────────────────────
echo "[ARTIFACT-INSTALL] Copying templates..."
for tmpl_file in "$TEMPLATES_SRC/"*.html; do
    [ -f "$tmpl_file" ] || continue
    name="$(basename "$tmpl_file")"
    docker cp "$tmpl_file" "$CONTAINER:$TEMPLATES_DEST/$name"
    echo "  template: $name"
done

# ── Syntax check ──────────────────────────────────────────────────────────────
echo "[ARTIFACT-INSTALL] Syntax check..."
docker exec "$CONTAINER" sh -c \
    "/opt/venv-a0/bin/python3 -m py_compile '$TOOL_DEST' && echo '  OK: artifact_create.py'"

# ── Clear pycache ─────────────────────────────────────────────────────────────
docker exec "$CONTAINER" sh -c \
    "rm -f /a0/usr/plugins/exocortex/tools/__pycache__/artifact_create.cpython-312.pyc" 2>/dev/null || true

echo ""
echo "[ARTIFACT-INSTALL] Done."
echo "  Tool:      $TOOL_DEST"
echo "  Templates: $TEMPLATES_DEST"
echo "  Output:    $OUTPUT_DEST"
echo ""

# Summary of what's installed
TEMPLATES=$(docker exec "$CONTAINER" sh -c "ls '$TEMPLATES_DEST'/*.html 2>/dev/null | xargs -I{} basename {} .html | tr '\n' ' '" 2>/dev/null || echo "(none)")
THEMES=$(docker exec "$CONTAINER" sh -c "ls '$TEMPLATES_DEST/themes'/*.json 2>/dev/null | xargs -I{} basename {} .json | tr '\n' ' '" 2>/dev/null || echo "(none)")
echo "  Templates: $TEMPLATES"
echo "  Themes:    $THEMES"
echo ""
echo "  Test: artifact_create(template='dashboard', data={'title':'Test','cards':[{'name':'BST','status':'healthy','metric':'v3.3'}]})"
