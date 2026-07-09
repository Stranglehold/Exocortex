#!/bin/bash
# install_agentevolver.sh
# Deploys the AgentEvolver Self-Improvement plugin to the persistent plugin path.
#
# Target: /a0/usr/plugins/agentevolver_self_improvement/   (uniform across containers)
#
# WHY THIS EXISTS (DEC-030 lesson): this plugin was originally hand-placed on the
# containers and was NOT in the install pipeline. A rebuild silently dropped it on
# v17 — Phase 5 of sleep consolidation then logged "engine unavailable" every cycle
# (see sleep_consolidation.run_phase5_consolidation). Folding it into install_all.sh
# makes the self-improvement engine a first-class, reproducible part of the stack:
# "if a rebuild drops it, it wasn't architecture — it was luck." (Opus, Call 1.)
#
# The SelfImprovementEngine (helpers/self_improvement.py) is imported by sleep
# consolidation Phase 5 to record failure experiences. It makes NO LLM calls
# (pure stdlib, JSON-backed) and registers NO turn-path extension/tool — so it is
# friction-neutral for cost-sensitive containers. Only the background sleep path
# touches it.
#
# CODE files overwrite (keep current). DATA files deploy ONLY IF MISSING — an agent's
# accumulated experiences/tasks/stats must never be wiped by a re-run.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONTAINER="${CONTAINER:-exocortex_v17}"
SRC="$SCRIPT_DIR/plugins/agentevolver_self_improvement"
DEST="/a0/usr/plugins/agentevolver_self_improvement"

# On Windows Git Bash, docker exec args with Unix paths get MSYS-translated.
_exec() { MSYS_NO_PATHCONV=1 docker exec "$@"; }

ERRORS=0

echo ""
echo "━━━ AgentEvolver Self-Improvement — Install ($CONTAINER) ━━━"
echo "  Source: $SRC"
echo "  Target: $DEST"

if [ ! -d "$SRC" ]; then
  echo "  ERR   vendored plugin not found at $SRC"
  exit 1
fi

# ── Directory structure ───────────────────────────────────────────────────────
_exec "$CONTAINER" mkdir -p \
  "$DEST/helpers" "$DEST/tools" "$DEST/webui" "$DEST/data"

# ── Deploy code (overwrite — keep current) ────────────────────────────────────
# Enumerate files individually so a host-side run and an in-container (docker-shim)
# run behave the same; avoids relying on directory-copy semantics.
CODE_FILES=(
  "hooks.py"
  "plugin.yaml"
  "index.yaml"
  "LICENSE"
  "README.md"
  "test_plugin.py"
  "helpers/__init__.py"
  "helpers/self_improvement.py"
  "tools/__init__.py"
  "tools/self_questioning_tool.py"
  "webui/config.html"
  "webui/thumbnail.jpg"
)
deployed=0
for rel in "${CODE_FILES[@]}"; do
  if [ -f "$SRC/$rel" ]; then
    docker cp "$SRC/$rel" "$CONTAINER:$DEST/$rel" 2>/dev/null \
      && deployed=$((deployed + 1)) \
      || { echo "  ERR   $rel — deploy failed"; ERRORS=$((ERRORS + 1)); }
  fi
done
echo "  OK    code: $deployed files deployed (overwrite)"

# ── Deploy data ONLY IF MISSING (preserve accumulated experiences) ────────────
data_new=0
data_kept=0
for f in experiences.json tasks.json stats.json; do
  if _exec "$CONTAINER" test -f "$DEST/data/$f" 2>/dev/null; then
    data_kept=$((data_kept + 1))
  else
    docker cp "$SRC/data/$f" "$CONTAINER:$DEST/data/$f" 2>/dev/null \
      && data_new=$((data_new + 1)) \
      || { echo "  ERR   data/$f — deploy failed"; ERRORS=$((ERRORS + 1)); }
  fi
done
echo "  OK    data: $data_new initialized fresh, $data_kept preserved (existing)"

# ── Clear pycache so new code loads ───────────────────────────────────────────
_exec "$CONTAINER" sh -c "rm -rf '$DEST/helpers/__pycache__' '$DEST/tools/__pycache__'" 2>/dev/null || true

# ── Syntax check (host-side, on the repo source) ──────────────────────────────
if command -v python3 &>/dev/null; then
  for f in helpers/self_improvement.py tools/self_questioning_tool.py hooks.py; do
    python3 -m py_compile "$SRC/$f" \
      && echo "  OK    $f syntax check" \
      || { echo "  ERR   $f syntax check failed"; ERRORS=$((ERRORS + 1)); }
  done
fi

# ── Verify import via Phase 5's exact load path ───────────────────────────────
if _exec "$CONTAINER" python3 -c "
import sys; sys.path.insert(0, '$DEST/helpers')
from self_improvement import SelfImprovementEngine
from pathlib import Path
SelfImprovementEngine(Path('$DEST'))
print('  OK    SelfImprovementEngine imports + instantiates in container')
" 2>/dev/null; then :; else
  echo "  ERR   in-container import check failed"
  ERRORS=$((ERRORS + 1))
fi

echo ""
if [ "$ERRORS" -eq 0 ]; then
  echo "  AgentEvolver plugin installed successfully."
else
  echo "  $ERRORS error(s) during install. Review output above."
  exit 1
fi
