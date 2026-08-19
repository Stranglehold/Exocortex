#!/usr/bin/env bash
# install_theme_editor.sh — Deploy the visual theme editor to Agent Zero
# Files deployed:
#   /a0/webui/js/theme-editor.js          (new modal editor)
#   /a0/webui/js/themes.js                (adds applyConfig() for live preview)
#   /a0/python/api/api_theme_save.py      (POST /api_theme_save)
#   /a0/python/api/api_theme_upload.py    (POST /api_theme_upload)
#   /a0/webui/index.html                  (inject <script> tag before </body>)

set -e

CONTAINER="${1:-${CONTAINER:-exocortex_v16}}"
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PATCHES="$REPO_DIR/patches"

echo "[theme-editor] Deploying to container: $CONTAINER"

# 1. Theme editor JS
docker cp "$PATCHES/webui/js/theme-editor.js" \
    "$CONTAINER:/a0/webui/js/theme-editor.js"
echo "[theme-editor] theme-editor.js -> /a0/webui/js/"

# 2. Updated themes.js (adds applyConfig)
docker cp "$PATCHES/webui/js/themes.js" \
    "$CONTAINER:/a0/webui/js/themes.js"
echo "[theme-editor] themes.js -> /a0/webui/js/"

# 3. API handlers
# ── STRIPPED 2026-08-19 (Tier 1.1): dead root; the plugin walk deploys these ──
# Both handlers went to /a0/python/api, which is absent in stock A0 v2.9. They ship
# in plugins/_exocortex/api/ (api_theme_save.py, api_theme_upload.py) and register
# at /api/plugins/_exocortex/<module>. The webui assets above are outside the
# plugin and are kept untouched.
if false; then
    docker cp "$PATCHES/python/api/api_theme_save.py" \
        "$CONTAINER:/a0/python/api/api_theme_save.py"
    docker cp "$PATCHES/python/api/api_theme_upload.py" \
        "$CONTAINER:/a0/python/api/api_theme_upload.py"
fi
echo "[theme-editor] api handlers: deployed by the plugin walk"

# 4. Inject <script> tag into index.html (idempotent)
SCRIPT_TAG='    <script src="js/theme-editor.js"></script>'
ALREADY=$(docker exec "$CONTAINER" sh -c \
    'grep -c "theme-editor.js" /a0/webui/index.html 2>/dev/null || true')

if [ "$ALREADY" -gt "0" ]; then
    echo "[theme-editor] index.html already has theme-editor.js — skipping injection"
else
    docker exec "$CONTAINER" sh -c \
        "sed -i 's|</body>|    <script src=\"js/theme-editor.js\"></script>\n</body>|' /a0/webui/index.html"
    echo "[theme-editor] Injected <script src='js/theme-editor.js'></script> into index.html"
fi

# 5. Syntax check — REMOVED 2026-08-19 (Tier 1.1)
# This compiled /a0/python/api/api_theme_*.py, the dead root this script no longer
# writes to, so it failed the whole step once the deploy was stripped. Not
# re-pointed at the plugin copies either: the walk runs LAST in install_all.sh, so
# on a fresh install those files do not exist yet at this point. The handlers are
# verified by scripts/verify_plugin_parity.py after the walk instead — one check,
# after the authoritative deploy, rather than a partial one before it.

echo ""
echo "[theme-editor] NOTE: API handlers require a container restart to be registered."
echo "[theme-editor] Run: docker restart $CONTAINER"
echo "[theme-editor] Then reload the web UI and use Ctrl+Shift+T to open the editor."
