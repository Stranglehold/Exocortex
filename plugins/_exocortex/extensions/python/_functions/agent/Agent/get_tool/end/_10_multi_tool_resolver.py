"""
Multi-Tool File Resolver
========================
Hook: _functions/agent/Agent/get_tool/end

When Agent Zero dispatches a tool, it looks for {tool_name}.py. This
works for single-class tool files but fails for multi-class files where
one .py file contains many Tool subclasses (oss.py, swarmfish.py,
investigation_tools.py, agentevolver.py, etc.).

This extension intercepts 'Unknown' tool results and searches all enabled
plugin tool files for a Tool subclass whose snake_case name matches the
requested tool name. If found, it swaps Unknown for the real tool class.

No LLM calls. Runs only when the primary dispatch returns Unknown.
"""

import glob
import importlib.util
import inspect
import os
import re
import sys
from typing import Any

from helpers.extension import Extension

# Plugin tool glob -- all plugin tool dirs
_TOOLS_GLOB = "/a0/usr/plugins/*/tools/*.py"

# Cache: tool_name -> class (populated on first miss)
_TOOL_CLASS_CACHE: dict[str, Any] = {}
_SCAN_DONE = False


def _to_snake(name: str) -> str:
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", name).lower()


def _load_module_from_path(path: str):
    """Import a .py file as a module without side effects from double-import."""
    abs_path = os.path.abspath(path)
    mod_name = "exo_tool_" + re.sub(r"[^\w]", "_", abs_path)
    if mod_name in sys.modules:
        return sys.modules[mod_name]
    spec = importlib.util.spec_from_file_location(mod_name, abs_path)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    try:
        spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    except Exception as exc:
        print(f"[TOOL-ROUTE] LOAD FAIL {os.path.basename(path)}: {exc}", flush=True)
        del sys.modules[mod_name]
        return None
    return mod


def _build_cache():
    """Scan all plugin tool files and populate _TOOL_CLASS_CACHE."""
    global _SCAN_DONE
    if _SCAN_DONE:
        return

    from helpers.tool import Tool

    files_found = sorted(glob.glob(_TOOLS_GLOB))

    for path in files_found:
        fname = os.path.basename(path)
        if fname.startswith("_"):
            continue
        mod = _load_module_from_path(path)
        if mod is None:
            continue
        for _name, cls in inspect.getmembers(mod, inspect.isclass):
            if cls is Tool:
                continue
            try:
                if not issubclass(cls, Tool):
                    continue
            except TypeError:
                continue
            snake = _to_snake(cls.__name__)
            if snake not in _TOOL_CLASS_CACHE:
                _TOOL_CLASS_CACHE[snake] = cls

    _SCAN_DONE = True
    print(f"[TOOL-ROUTE] Cache built: {len(_TOOL_CLASS_CACHE)} tools from plugins", flush=True)


class MultiToolResolver(Extension):
    """Swap Unknown for the real tool class if one exists in any plugin file."""

    def execute(self, data: dict | None = None, **kwargs) -> None:
        if data is None:
            return

        result = data.get("result")
        if result is None:
            return

        # Only intervene for Unknown tools
        from tools.unknown import Unknown
        if not isinstance(result, Unknown):
            return

        tool_name: str = getattr(result, "name", "") or ""
        if not tool_name:
            return

        # Lazily build the cache on first miss
        _build_cache()

        tool_class = _TOOL_CLASS_CACHE.get(tool_name)
        if tool_class is None:
            return

        real_tool = tool_class(
            agent=result.agent,
            name=result.name,
            method=result.method,
            args=result.args,
            message=result.message,
            loop_data=result.loop_data,
        )
        data["result"] = real_tool
        print(f"[TOOL-ROUTE] Resolved '{tool_name}' -> {tool_class.__name__}", flush=True)
