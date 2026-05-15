#!/usr/bin/env python3
"""
Standalone KV cache pre-warmer — runs inside the exocortex_v16 container
via `docker exec -d exocortex_v16 python3 /a0/usr/Exocortex/inference/warm_cache.py`.

Called from start_mtp.bat via warm_cache_trigger.ps1, in background, after the
MTP server health check passes. By the time Jake opens A0 and types his first
message, the KV cache already holds the static system prompt. Turn 1 only needs
to prefill the delta (dynamic BST/memory injections + Jake's message ~300 tokens)
instead of the full 12-15K token prompt.

This is a PARTIAL warm-up (static prompt only, no runtime extension injections).
The _71_cache_warmer.py extension provides a FULL warm-up at Turn 1 if needed.

Prompt assembly mirrors _10_main_prompt.py + _11_tools_prompt.py:
  Priority order: profile path > user path > base path
  Handles {{ include "file.md" }} recursive template expansion.
"""

import sys
import os
import re
import glob
import json
import urllib.request
import urllib.error
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [CACHE-WARM] %(message)s",
    stream=sys.stdout,
    force=True,
)
log = logging.getLogger(__name__)

SERVER_URL = "http://host.docker.internal:1235"

# Prompt search paths in priority order (mirrors subagents.get_paths)
PROMPT_DIRS = [
    "/a0/usr/agents/agent0/prompts",  # profile path (overrides)
    "/a0/usr/prompts",                # user path
    "/a0/prompts",                    # base path
]

# {{ include "filename.md" }} pattern
_INCLUDE_RE = re.compile(r'\{\{\s*include\s+"([^"]+)"\s*\}\}')


def find_file(filename: str) -> str | None:
    """Return the highest-priority path for the given filename."""
    for d in PROMPT_DIRS:
        path = os.path.join(d, filename)
        if os.path.isfile(path):
            return path
    return None


def read_and_expand(filename: str, depth: int = 0) -> str:
    """Read a prompt file and recursively expand {{ include "..." }} directives."""
    if depth > 10:
        return ""  # guard against runaway recursion

    path = find_file(filename)
    if path is None:
        log.warning("Not found: %s", filename)
        return ""

    with open(path, encoding="utf-8") as f:
        content = f.read()

    def _expand(m: re.Match) -> str:
        return read_and_expand(m.group(1), depth + 1)

    return _INCLUDE_RE.sub(_expand, content)


def get_unique_tool_files() -> list[str]:
    """Return unique tool filenames in priority order (profile path wins)."""
    seen: set[str] = set()
    result: list[str] = []
    for d in PROMPT_DIRS:
        pattern = os.path.join(d, "agent.system.tool.*.md")
        for path in sorted(glob.glob(pattern)):
            name = os.path.basename(path)
            if name not in seen:
                seen.add(name)
                result.append(name)
    return result


def build_system_prompt() -> str:
    parts: list[str] = []

    # Part 1: main prompt with recursive include expansion
    main_text = read_and_expand("agent.system.main.md")
    if main_text.strip():
        parts.append(main_text.strip())

    # Part 2: tool prompts wrapped in agent.system.tools.md template
    tool_files = get_unique_tool_files()
    tools: list[str] = []
    for tool_file in tool_files:
        text = read_and_expand(tool_file)
        if text.strip():
            tools.append(text.strip())

    tools_str = "\n\n".join(tools)

    wrapper_path = find_file("agent.system.tools.md")
    if wrapper_path:
        with open(wrapper_path, encoding="utf-8") as f:
            wrapper = f.read()
        tools_section = wrapper.replace("{{tools}}", tools_str).strip()
    else:
        tools_section = tools_str

    if tools_section:
        parts.append(tools_section)

    return "\n\n".join(parts)


def send_warmup(system_prompt: str) -> int:
    payload = json.dumps({
        "model": "qwen",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Respond with OK."},
        ],
        "max_tokens": 1,
        "enable_thinking": False,
        "cache_prompt": True,
        "stream": False,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{SERVER_URL}/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return body.get("usage", {}).get("prompt_tokens", 0)
    except urllib.error.URLError as e:
        log.error("Request failed: %s", e)
        return 0


def main():
    log.info("Building static system prompt...")
    t0 = time.time()

    system_prompt = build_system_prompt()
    char_count = len(system_prompt)
    token_est = int(char_count / 4)  # ~4 chars/token for English text
    log.info(
        "Prompt: %d chars (~%d tokens est). Sending warm-up request to %s...",
        char_count,
        token_est,
        SERVER_URL,
    )

    prompt_tokens = send_warmup(system_prompt)
    elapsed = time.time() - t0

    if prompt_tokens:
        log.info(
            "Complete in %.1fs. Server prefilled %d tokens. KV cache is hot.",
            elapsed,
            prompt_tokens,
        )
    else:
        log.warning("Warm-up may have failed (%.1fs elapsed, 0 tokens returned).", elapsed)


if __name__ == "__main__":
    main()
