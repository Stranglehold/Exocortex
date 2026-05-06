#!/usr/bin/env bash
# install_core_patches.sh
# Deploy core Agent Zero file patches to the active container.
#
# v1.13 paths:
#   /a0/helpers/         — still present (extract_tools.py, etc.)
#   /a0/prompts/         — still present
#   /a0/api/             — still present
#   /a0/tools/           — REMOVED in v1.13; tools are now in /a0/plugins/_*/tools/
#   browser_agent.py     — REMOVED: browser is now /a0/plugins/_browser/tools/browser.py
#                          and /a0/plugins/_browser_agent/ handles AI-guided browsing
#   captcha_solver.py    — REMOVED: needs adaptation to new browser plugin architecture
#
# Patches:
#   patches/helpers/extract_tools.py
#     → adds plain-text fallback to json_parse_dirty()
#     → reasoning-distilled models no longer trigger the misformat loop
#       when they respond in natural language instead of JSON
#
#   patches/prompts/fw.msg_repeat.md
#     → replaces verbose 3-option loop message with: "call a subagent"
#     → eliminates the option menu that lets the agent keep spinning
#
#   patches/prompts/fw.msg_misformat.md (NEW)
#     → replaces generic "you have misformatted" with truncation guidance
#     → explains output-token truncation and append-mode file writes
#     → breaks the infinite misformat loop caused by oversized code payloads
#
#   patches/prompts/agent.system.main.communication.md
#     → clarifies that plain text is accepted for conversational replies
#
#   extensions/response_stream_chunk/_21_plain_text_response.py
#     → creates browser log item for plain text responses during streaming
#     → fixes responses not showing in web UI for reasoning-distilled models
#
#   extensions/before_main_llm_call/_18_memory_catalog.py
#     → injects compact memory domain catalog once at session start
#     → gives agent visibility into what's stored before querying blind
#
#   /a0/agent.py (validate_tool_request)
#     → A0's validator rejects tool_args={} (empty dict is falsy in Python)
#     → Patch: `not tool_args` → `tool_args is None` so no-arg tools work
#
# Usage: ./scripts/install_core_patches.sh [container_name]
# Default container: flamboyant_bell

set -e

CONTAINER="${1:-flamboyant_bell}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PATCH_DIR="$REPO_ROOT/patches"
PLUGIN_EXT="$CONTAINER:/a0/usr/plugins/exocortex/extensions/python"

# Prevent Git Bash on Windows from translating Unix paths in docker exec arguments.
_exec() { MSYS_NO_PATHCONV=1 docker exec "$@"; }

echo "[PATCH] Deploying core patches to container: $CONTAINER"

# ── 0. Tool: browser_agent.py + captcha_solver.py ────────────────────────────
# NOTE v1.13: /a0/tools/ no longer exists. Browser is now a plugin at
#   /a0/plugins/_browser/tools/browser.py (direct control)
#   /a0/plugins/_browser_agent/tools/ (AI-guided browsing, compiled)
# browser_agent.py and captcha_solver.py need adaptation for the new plugin
# architecture before they can be restored. Skipped for now.
echo "[PATCH] Skipping browser_agent.py/captcha_solver.py — v1.13 plugin architecture change (needs redesign)."

# ── 1. Python helper: extract_tools.py ────────────────────────────────────────

HELPER_SRC="$PATCH_DIR/helpers/extract_tools.py"
HELPER_DST="/a0/helpers/extract_tools.py"
HELPER_PYCACHE="/a0/helpers/__pycache__"

if [ -f "$HELPER_SRC" ]; then
  _exec "$CONTAINER" mkdir -p /a0/helpers
  docker cp "$HELPER_SRC" "$CONTAINER:$HELPER_DST"
  _exec "$CONTAINER" bash -c "rm -rf '$HELPER_PYCACHE'" 2>/dev/null || true
  _exec "$CONTAINER" bash -c "/opt/venv-a0/bin/python3 -m py_compile '$HELPER_DST' && echo '[PATCH] extract_tools.py OK'"
  echo "[PATCH] helpers/extract_tools.py deployed."
else
  echo "[PATCH] WARNING: $HELPER_SRC not found — skipped."
fi

# ── 1b. Python helper: provider_interface.py (max_tokens 4096→16384) ──────────

PROVIDER_SRC="$PATCH_DIR/helpers/provider_interface.py"
PROVIDER_DST="/a0/helpers/provider_interface.py"

if [ -f "$PROVIDER_SRC" ]; then
  docker cp "$PROVIDER_SRC" "$CONTAINER:$PROVIDER_DST"
  _exec "$CONTAINER" bash -c "rm -rf '$HELPER_PYCACHE'" 2>/dev/null || true
  _exec "$CONTAINER" bash -c "/opt/venv-a0/bin/python3 -m py_compile '$PROVIDER_DST' && echo '[PATCH] provider_interface.py OK'"
  echo "[PATCH] helpers/provider_interface.py deployed."
else
  echo "[PATCH] WARNING: $PROVIDER_SRC not found — skipped."
fi

# ── 2. Prompt: fw.msg_repeat.md (loop detected → call subagent) ──────────────

REPEAT_SRC="$PATCH_DIR/prompts/fw.msg_repeat.md"
REPEAT_DST="/a0/prompts/fw.msg_repeat.md"

if [ -f "$REPEAT_SRC" ]; then
  docker cp "$REPEAT_SRC" "$CONTAINER:$REPEAT_DST"
  echo "[PATCH] prompts/fw.msg_repeat.md deployed."
else
  echo "[PATCH] WARNING: $REPEAT_SRC not found — skipped."
fi

# ── 2a. Prompt: fw.msg_misformat.md (truncated payload + format guidance) ────
# Replaces generic "you have misformatted" with actionable guidance explaining
# output-token truncation and how to write large files using append mode.

MISFORMAT_SRC="$PATCH_DIR/prompts/fw.msg_misformat.md"
MISFORMAT_DST="/a0/prompts/fw.msg_misformat.md"

if [ -f "$MISFORMAT_SRC" ]; then
  docker cp "$MISFORMAT_SRC" "$CONTAINER:$MISFORMAT_DST"
  echo "[PATCH] prompts/fw.msg_misformat.md deployed (truncation guidance)."
else
  echo "[PATCH] WARNING: $MISFORMAT_SRC not found — skipped."
fi

# ── 2b. Prompt: agent.system.main.communication.md ───────────────────────────

PROMPT_SRC="$PATCH_DIR/prompts/agent.system.main.communication.md"
PROMPT_DST="/a0/prompts/agent.system.main.communication.md"

if [ -f "$PROMPT_SRC" ]; then
  docker cp "$PROMPT_SRC" "$CONTAINER:$PROMPT_DST"
  echo "[PATCH] prompts/agent.system.main.communication.md deployed."
else
  echo "[PATCH] WARNING: $PROMPT_SRC not found — skipped."
fi

# ── 2d. Prompt: agent.system.datetime.md (safer format for local models) ─────
# Original: "- current datetime: {{date_time}}\n- rely on this info always up to date"
# Local models (Gemma 4) treat the "- key: value" bullet pattern as JSON and
# leak the datetime string into tool_args as a garbage key. Replaced with a
# single declarative sentence that is clearly not JSON structure.

DATETIME_SRC="$PATCH_DIR/prompts/agent.system.datetime.md"
DATETIME_DST="/a0/prompts/agent.system.datetime.md"

if [ -f "$DATETIME_SRC" ]; then
  docker cp "$DATETIME_SRC" "$CONTAINER:$DATETIME_DST"
  echo "[PATCH] prompts/agent.system.datetime.md deployed (safer format)."
else
  echo "[PATCH] WARNING: $DATETIME_SRC not found — skipped."
fi

# ── 2c. Prompt: browser_agent.system.md (CAPTCHA guidance) ───────────────────

BROWSER_PROMPT_SRC="$PATCH_DIR/prompts/browser_agent.system.md"
BROWSER_PROMPT_DST="/a0/prompts/browser_agent.system.md"

if [ -f "$BROWSER_PROMPT_SRC" ]; then
  docker cp "$BROWSER_PROMPT_SRC" "$CONTAINER:$BROWSER_PROMPT_DST"
  echo "[PATCH] prompts/browser_agent.system.md (CAPTCHA guidance) deployed."
else
  echo "[PATCH] WARNING: $BROWSER_PROMPT_SRC not found — skipped."
fi

# ── 3. Extension: _21_plain_text_response.py ─────────────────────────────────
# v1.6: profile path only (extensions/python/ subdirectory)

EXT_SRC="$REPO_ROOT/extensions/response_stream_chunk/_21_plain_text_response.py"
EXT_PROFILE_DST="/a0/usr/plugins/exocortex/extensions/python/response_stream_chunk/_21_plain_text_response.py"
EXT_PROFILE_PYCACHE="/a0/usr/plugins/exocortex/extensions/python/response_stream_chunk/__pycache__"

if [ -f "$EXT_SRC" ]; then
  _exec "$CONTAINER" mkdir -p /a0/usr/plugins/exocortex/extensions/python/response_stream_chunk
  docker cp "$EXT_SRC" "$CONTAINER:$EXT_PROFILE_DST"
  _exec "$CONTAINER" bash -c "rm -rf '$EXT_PROFILE_PYCACHE'" 2>/dev/null || true
  _exec "$CONTAINER" bash -c "/opt/venv-a0/bin/python3 -m py_compile '$EXT_PROFILE_DST' && echo '[PATCH] _21_plain_text_response.py OK'"
  echo "[PATCH] extensions/response_stream_chunk/_21_plain_text_response.py deployed (profile path)."
else
  echo "[PATCH] WARNING: $EXT_SRC not found — skipped."
fi

# ── 3b. Extension: _20_clear_generating_content.py ───────────────────────────
# Clears log_item_generating.content at response_stream_end so the webUI
# doesn't render the raw streaming JSON for every tool call turn.

CLR_SRC="$REPO_ROOT/extensions/response_stream_end/_20_clear_generating_content.py"
CLR_PROFILE_DST="/a0/usr/plugins/exocortex/extensions/python/response_stream_end/_20_clear_generating_content.py"
CLR_PROFILE_PYCACHE="/a0/usr/plugins/exocortex/extensions/python/response_stream_end/__pycache__"

if [ -f "$CLR_SRC" ]; then
  _exec "$CONTAINER" mkdir -p /a0/usr/plugins/exocortex/extensions/python/response_stream_end
  docker cp "$CLR_SRC" "$CONTAINER:$CLR_PROFILE_DST"
  _exec "$CONTAINER" bash -c "rm -rf '$CLR_PROFILE_PYCACHE'" 2>/dev/null || true
  _exec "$CONTAINER" bash -c "/opt/venv-a0/bin/python3 -m py_compile '$CLR_PROFILE_DST' && echo '[PATCH] _20_clear_generating_content.py OK'"
  echo "[PATCH] extensions/response_stream_end/_20_clear_generating_content.py deployed (profile path)."
else
  echo "[PATCH] WARNING: $CLR_SRC not found — skipped."
fi

# ── 4. Extension: _18_memory_catalog.py ──────────────────────────────────────
# v1.6: profile path only

CAT_SRC="$REPO_ROOT/extensions/before_main_llm_call/_18_memory_catalog.py"
CAT_PROFILE_DST="/a0/usr/plugins/exocortex/extensions/python/before_main_llm_call/_18_memory_catalog.py"
CAT_PROFILE_PYCACHE="/a0/usr/plugins/exocortex/extensions/python/before_main_llm_call/__pycache__"

if [ -f "$CAT_SRC" ]; then
  _exec "$CONTAINER" mkdir -p /a0/usr/plugins/exocortex/extensions/python/before_main_llm_call
  docker cp "$CAT_SRC" "$CONTAINER:$CAT_PROFILE_DST"
  _exec "$CONTAINER" bash -c "rm -rf '$CAT_PROFILE_PYCACHE'" 2>/dev/null || true
  _exec "$CONTAINER" bash -c "/opt/venv-a0/bin/python3 -m py_compile '$CAT_PROFILE_DST' && echo '[PATCH] _18_memory_catalog.py OK'"
  echo "[PATCH] extensions/before_main_llm_call/_18_memory_catalog.py deployed (profile path)."
else
  echo "[PATCH] WARNING: $CAT_SRC not found — skipped."
fi

# ── 5. API: artifacts_list.py (remove polling noise) ─────────────────────────
# Removes the PrintStyle.print() success log that fires on every 30s poll
# from every open browser tab, flooding docker logs and obscuring responses.

ARTIFACTS_SRC="$PATCH_DIR/api/artifacts_list.py"
ARTIFACTS_DST="/a0/api/artifacts_list.py"
ARTIFACTS_PYCACHE="/a0/api/__pycache__"

if [ -f "$ARTIFACTS_SRC" ]; then
  _exec "$CONTAINER" mkdir -p /a0/api
  docker cp "$ARTIFACTS_SRC" "$CONTAINER:$ARTIFACTS_DST"
  _exec "$CONTAINER" bash -c "rm -rf '$ARTIFACTS_PYCACHE'" 2>/dev/null || true
  _exec "$CONTAINER" bash -c "/opt/venv-a0/bin/python3 -m py_compile '$ARTIFACTS_DST' && echo '[PATCH] artifacts_list.py OK'"
  echo "[PATCH] api/artifacts_list.py deployed (polling noise removed)."
else
  echo "[PATCH] WARNING: $ARTIFACTS_SRC not found — skipped."
fi

# ── 6. WebUI CSS: process-group.css (hide util process steps) ────────────────
# Uncomments .process-step.message-util { display: none; } so that "util"-type
# log items created by Exocortex extensions are hidden from the chat UI.

CSS_SRC="$PATCH_DIR/webui/components/messages/process-group/process-group.css"
CSS_DST="/a0/webui/components/messages/process-group/process-group.css"

if [ -f "$CSS_SRC" ]; then
  docker cp "$CSS_SRC" "$CONTAINER:$CSS_DST"
  echo "[PATCH] webui/components/messages/process-group/process-group.css deployed."
else
  echo "[PATCH] WARNING: $CSS_SRC not found — skipped."
fi

# ── 7. agent.py: validate_tool_request empty-args fix ────────────────────────
# v1.13 NOTE: validate_tool_request now delegates to normalize_tool_request()
# in extract_tools.py, which uses isinstance() checks (not falsiness).
# The empty-dict bug is already fixed in v1.13 + our extract_tools.py patch.
# Keeping the old pattern check for pre-v1.13 containers.

_exec "$CONTAINER" python3 -c "
path = '/a0/agent.py'
with open(path, 'r') as f:
    content = f.read()
old = 'if not tool_request.get(\"tool_args\") or not isinstance(tool_request.get(\"tool_args\"), dict):'
new = 'if tool_request.get(\"tool_args\") is None or not isinstance(tool_request.get(\"tool_args\", {}), dict):'
if old in content:
    content = content.replace(old, new, 1)
    with open(path, 'w') as f:
        f.write(content)
    print('[PATCH] agent.py validate_tool_request: empty-args fix applied.')
elif new in content:
    print('[PATCH] agent.py validate_tool_request: already patched, skipped.')
else:
    print('[PATCH] v1.13+: validate_tool_request delegates to normalize_tool_request() — no patch needed.')
"

# ── 8. Extension: _20_meta_reasoning_gate.py ─────────────────────────────────
# Deploys to all known active profile paths. Active path confirmed:
#   /a0/usr/agents/agent0/extensions/python/tool_execute_before/
# Other paths deployed as fallback. pycache cleared at each location.
# Changes: content->code alias, text_editor_remote intercept,
#          truncation-specific message for missing code arg, strip_unknown_args.

GATE_SRC="$REPO_ROOT/extensions/tool_execute_before/_20_meta_reasoning_gate.py"

GATE_PATHS=(
  "/a0/usr/plugins/exocortex/extensions/python/tool_execute_before/_20_meta_reasoning_gate.py"
  "/a0/usr/Exocortex/extensions/tool_execute_before/_20_meta_reasoning_gate.py"
  "/a0/usr/agents/agent0/extensions/tool_execute_before/_20_meta_reasoning_gate.py"
  "/a0/usr/agents/agent0/extensions/python/tool_execute_before/_20_meta_reasoning_gate.py"
)

if [ -f "$GATE_SRC" ]; then
  for DST in "${GATE_PATHS[@]}"; do
    DIR=$(dirname "$DST")
    _exec "$CONTAINER" mkdir -p "$DIR"
    docker cp "$GATE_SRC" "$CONTAINER:$DST"
    CACHE="$DIR/__pycache__"
    _exec "$CONTAINER" bash -c "rm -rf '$CACHE'" 2>/dev/null || true
  done
  _exec "$CONTAINER" bash -c "/opt/venv-a0/bin/python3 -m py_compile '${GATE_PATHS[3]}' && echo '[PATCH] _20_meta_reasoning_gate.py OK'"
  echo "[PATCH] extensions/tool_execute_before/_20_meta_reasoning_gate.py deployed (all 4 profile paths)."
else
  echo "[PATCH] WARNING: $GATE_SRC not found — skipped."
fi

# ── 9. Memory consolidation: timeout + UI noise fix ──────────────────────────
# A0's default memory_consolidation.py uses PrintStyle().error() for timeout
# and exception paths, surfacing background-task failures into the agent's
# visible UI. Also uses a 60-second timeout that is too short when the local
# model is busy during inference.
#
# Fix: 60s → 180s timeout, PrintStyle().error() → logging.warning() for the
# two timeout/exception handlers in process_new_memory().

MEM_CON_SRC="$PATCH_DIR/plugins/_memory/helpers/memory_consolidation.py"
MEM_CON_DST="/a0/plugins/_memory/helpers/memory_consolidation.py"
MEM_CON_PYCACHE="/a0/plugins/_memory/helpers/__pycache__"

if [ -f "$MEM_CON_SRC" ]; then
  docker cp "$MEM_CON_SRC" "$CONTAINER:$MEM_CON_DST"
  _exec "$CONTAINER" bash -c "rm -rf '$MEM_CON_PYCACHE'" 2>/dev/null || true
  _exec "$CONTAINER" bash -c "/opt/venv-a0/bin/python3 -m py_compile '$MEM_CON_DST' && echo '[PATCH] memory_consolidation.py OK'"
  echo "[PATCH] plugins/_memory/helpers/memory_consolidation.py deployed (timeout 180s, errors silent)."
else
  echo "[PATCH] WARNING: $MEM_CON_SRC not found — skipped."
fi

echo "[PATCH] Done. Restart agent-zero or start a fresh chat to load changes."
