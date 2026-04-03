"""
theme_author.py — Agent Zero WebUI Theme Authoring Tool
========================================================

Creates, validates, and deploys new themes to the Exocortex theme system.

Use this tool to deploy a completed theme JSON. Design the JSON according to
THEME_AUTHORING_GUIDE.md, then call this tool with the complete JSON to
validate and deploy in one step.

Actions
-------
deploy   — Validate JSON, write theme file, and add to index.json.
           Returns success with theme name, or validation errors without deploying.

validate — Validate JSON only. Returns "VALID" or a list of specific errors.
           Does not write any files.

list     — List all currently installed themes with name and description.

remove   — Remove a theme by key: deletes the JSON and removes from index.json.

Arguments
---------
action     : "deploy" | "validate" | "list" | "remove"
theme_key  : Filename key — lowercase, hyphens only, no .json suffix.
             Required for: deploy, validate, remove.
             Example: "my-theme", "snake-eater", "big-boss"
theme_json : Complete theme JSON as a string.
             Required for: deploy, validate.

Required JSON fields: name, author, description, version, colors, fonts, preview
Required color keys: background, text, text-muted, primary, secondary, accent,
  message-bg, highlight, message-text, panel, border, input, input-focus,
  chat-background, error-text, warning-text, table-row
Valid tiers (if present): palette, atmospheric, immersive
"""

import json
import os
import re

from helpers.tool import Tool, Response


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

THEMES_DIR   = "/a0/usr/plugins/exocortex/webui/themes"
THEMES_INDEX = "/a0/usr/plugins/exocortex/webui/themes/index.json"

REQUIRED_TOP_FIELDS = {"name", "author", "description", "version", "colors", "fonts", "preview"}

REQUIRED_COLOR_KEYS = {
    "background", "text", "text-muted", "primary", "secondary", "accent",
    "message-bg", "highlight", "message-text", "panel", "border", "input",
    "input-focus", "chat-background", "error-text", "warning-text", "table-row",
}

VALID_TIERS = {"palette", "atmospheric", "immersive"}

# Matches: #RGB, #RGBA, #RRGGBB, #RRGGBBAA, rgba(...)
COLOR_PATTERN = re.compile(r'^#[0-9a-fA-F]{3,8}$|^rgba\(')


# ---------------------------------------------------------------------------
# Tool class
# ---------------------------------------------------------------------------

class ThemeAuthor(Tool):
    """
    Deploy, validate, list, or remove Exocortex webUI themes (v1.6+).
    See module docstring for full usage guide.
    """

    async def execute(self, loop_data=None, **kwargs) -> Response:
        try:
            args = self.args if hasattr(self, "args") and self.args else kwargs
            action = str(args.get("action", "")).strip().lower()

            if action == "list":
                return Response(message=_list_themes(), break_loop=False)

            theme_key = str(args.get("theme_key", "")).strip().lower()
            if not theme_key and action in ("deploy", "validate", "remove"):
                return Response(
                    message="[THEME] Error: theme_key is required for this action.",
                    break_loop=False,
                )

            if action == "remove":
                return Response(message=_remove_theme(theme_key), break_loop=False)

            theme_json_str = str(args.get("theme_json", "")).strip()
            if not theme_json_str and action in ("deploy", "validate"):
                return Response(
                    message="[THEME] Error: theme_json is required for deploy/validate.",
                    break_loop=False,
                )

            if action == "validate":
                errors = _validate(theme_json_str)
                if errors:
                    msg = "[THEME] Validation errors:\n" + "\n".join(f"  - {e}" for e in errors)
                else:
                    msg = "[THEME] VALID — theme JSON passes all checks."
                return Response(message=msg, break_loop=False)

            if action == "deploy":
                return Response(message=_deploy(theme_key, theme_json_str), break_loop=False)

            return Response(
                message=f"[THEME] Unknown action '{action}'. Use: deploy, validate, list, remove.",
                break_loop=False,
            )

        except Exception as e:
            return Response(message=f"[THEME] Unexpected error: {e}", break_loop=False)


# ---------------------------------------------------------------------------
# Core operations
# ---------------------------------------------------------------------------

def _validate(theme_json_str: str) -> list:
    """Return list of error strings, empty if valid."""
    errors = []

    try:
        theme = json.loads(theme_json_str)
    except json.JSONDecodeError as e:
        return [f"Invalid JSON: {e}"]

    if not isinstance(theme, dict):
        return ["Theme must be a JSON object."]

    missing = REQUIRED_TOP_FIELDS - set(theme.keys())
    for f in sorted(missing):
        errors.append(f"Missing required field: {f}")

    colors = theme.get("colors", {})
    if isinstance(colors, dict):
        missing_colors = REQUIRED_COLOR_KEYS - set(colors.keys())
        for k in sorted(missing_colors):
            errors.append(f"Missing required color key: colors.{k}")

        for key, val in colors.items():
            if not isinstance(val, str):
                errors.append(f"Color value must be a string: colors.{key} = {val!r}")
            elif not COLOR_PATTERN.match(val):
                errors.append(
                    f"Invalid color format: colors.{key} = {val!r}  "
                    f"(must be #RGB, #RRGGBB, #RRGGBBAA, or rgba(...))"
                )
    else:
        errors.append("'colors' must be an object.")

    tier = theme.get("tier")
    if tier is not None and tier not in VALID_TIERS:
        errors.append(
            f"Invalid tier: {tier!r}. Must be one of: {', '.join(sorted(VALID_TIERS))}"
        )

    return errors


def _deploy(theme_key: str, theme_json_str: str) -> str:
    """Validate, write theme file, update index.json. Returns status message."""
    if not re.match(r'^[a-z0-9][a-z0-9-]*$', theme_key):
        return (
            f"[THEME] Error: invalid theme_key '{theme_key}'. "
            "Use lowercase letters, digits, and hyphens only."
        )

    errors = _validate(theme_json_str)
    if errors:
        return "[THEME] Validation failed — not deployed:\n" + "\n".join(
            f"  - {e}" for e in errors
        )

    theme = json.loads(theme_json_str)
    theme_name = theme.get("name", theme_key)

    dest_path = os.path.join(THEMES_DIR, f"{theme_key}.json")
    try:
        os.makedirs(THEMES_DIR, exist_ok=True)
        with open(dest_path, "w", encoding="utf-8") as f:
            json.dump(theme, f, indent=2, ensure_ascii=False)
    except OSError as e:
        return f"[THEME] Error writing theme file: {e}"

    index_result = _add_to_index(theme_key, theme)

    return (
        f"[THEME] Deployed '{theme_name}' as key '{theme_key}'.\n"
        f"  File: {dest_path}\n"
        f"  Index: {index_result}\n"
        f"  Reload the browser tab to see it in the sidebar theme picker."
    )


def _remove_theme(theme_key: str) -> str:
    """Delete theme JSON and remove from index.json."""
    theme_path = os.path.join(THEMES_DIR, f"{theme_key}.json")

    removed_file = False
    if os.path.exists(theme_path):
        try:
            os.remove(theme_path)
            removed_file = True
        except OSError as e:
            return f"[THEME] Error deleting theme file: {e}"

    index_result = _remove_from_index(theme_key)

    if removed_file:
        return f"[THEME] Removed theme '{theme_key}'.\n  Index: {index_result}"
    return (
        f"[THEME] Theme file '{theme_key}.json' not found "
        f"(may already be deleted).\n  Index: {index_result}"
    )


def _list_themes() -> str:
    """List all theme JSON files with name and description."""
    try:
        entries = []
        for fname in sorted(os.listdir(THEMES_DIR)):
            if not fname.endswith(".json") or fname in ("template.json", "index.json"):
                continue
            key = fname[:-5]
            try:
                with open(os.path.join(THEMES_DIR, fname), encoding="utf-8") as f:
                    data = json.load(f)
                name = data.get("name", key)
                desc = data.get("description", "")[:50]
                entries.append(f"  {key:<22}  {name:<24}  {desc}")
            except Exception as e:
                entries.append(f"  {key:<22}  (error reading: {e})")

        if not entries:
            return "[THEME] No themes installed."
        return "[THEME] Installed themes:\n" + "\n".join(entries)
    except Exception as e:
        return f"[THEME] Error listing themes: {e}"


# ---------------------------------------------------------------------------
# index.json helpers
# ---------------------------------------------------------------------------

def _load_index() -> dict:
    try:
        with open(THEMES_INDEX, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {"themes": []}


def _save_index(index: dict) -> str:
    try:
        with open(THEMES_INDEX, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
        return "index.json updated"
    except OSError as e:
        return f"could not write index.json: {e}"


def _add_to_index(theme_key: str, theme: dict) -> str:
    """Add or update entry for theme_key in index.json."""
    index = _load_index()
    themes = index.setdefault("themes", [])

    preview = theme.get("preview", {})
    entry = {
        "id":          theme_key,
        "name":        theme.get("name", theme_key),
        "description": theme.get("description", ""),
        "preview": {
            "background": preview.get("background", theme.get("colors", {}).get("background", "#000")),
            "text":       preview.get("text",       theme.get("colors", {}).get("text", "#fff")),
            "accent":     preview.get("accent",     theme.get("colors", {}).get("accent", "#888")),
        },
    }

    # Update if exists, else append
    for i, t in enumerate(themes):
        if t.get("id") == theme_key:
            themes[i] = entry
            return _save_index(index)

    themes.append(entry)
    return _save_index(index)


def _remove_from_index(theme_key: str) -> str:
    """Remove entry for theme_key from index.json."""
    index = _load_index()
    before = len(index.get("themes", []))
    index["themes"] = [t for t in index.get("themes", []) if t.get("id") != theme_key]
    after = len(index["themes"])

    if before == after:
        return f"'{theme_key}' not found in index.json (no change)"
    return _save_index(index)
