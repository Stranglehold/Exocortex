"""
theme_author.py — Agent Zero WebUI Theme Authoring Tool
========================================================

Creates, validates, and deploys new themes to the Agent Zero webUI.

Use this tool to deploy a completed theme JSON without manually copying files.
Design the theme JSON according to THEME_AUTHORING_GUIDE.md, then call this
tool with the complete JSON to validate and deploy it in one step.

Actions
-------
deploy   — Validate JSON and write to /a0/webui/themes/{key}.json,
           then add key to knownThemes in theme-store.js.
           Returns success with theme name, or validation errors without deploying.

validate — Validate JSON only. Returns "VALID" or a list of specific errors.
           Does not write any files.

list     — List all currently installed themes with name and tier.

remove   — Remove a theme by key: deletes the JSON and removes from knownThemes.

Arguments
---------
action     : "deploy" | "validate" | "list" | "remove"
theme_key  : Filename key — lowercase, hyphens only, no .json suffix.
             Required for: deploy, validate, remove.
             Example: "my-theme", "snake-eater", "big-boss"
theme_json : Complete theme JSON as a string.
             Required for: deploy, validate.

Examples
--------
Validate before deploying:
  action=validate, theme_key=my-theme, theme_json={...}

Deploy a new theme:
  action=deploy, theme_key=my-theme, theme_json={...}

List installed themes:
  action=list

Remove a theme:
  action=remove, theme_key=my-theme

Required JSON fields: name, author, description, version, colors, fonts, preview
Required color keys: background, text, text-muted, primary, secondary, accent,
  message-bg, highlight, message-text, panel, border, input, input-focus,
  chat-background, error-text, warning-text, table-row
Valid tiers (if present): palette, atmospheric, immersive
"""

import json
import os
import re

from python.helpers.tool import Tool, Response


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

THEMES_DIR = "/a0/webui/themes"
THEME_STORE_PATH = "/a0/webui/components/sidebar/themes/theme-store.js"

REQUIRED_TOP_FIELDS = {"name", "author", "description", "version", "colors", "fonts", "preview"}

REQUIRED_COLOR_KEYS = {
    "background", "text", "text-muted", "primary", "secondary", "accent",
    "message-bg", "highlight", "message-text", "panel", "border", "input",
    "input-focus", "chat-background", "error-text", "warning-text", "table-row",
}

VALID_TIERS = {"palette", "atmospheric", "immersive"}

# Matches: #RGB, #RGBA, #RRGGBB, #RRGGBBAA, rgba(...)
COLOR_PATTERN = re.compile(r'^#[0-9a-fA-F]{3,8}$|^rgba\(')

# Matches the knownThemes array in theme-store.js
KNOWN_THEMES_RE = re.compile(
    r"(const\s+knownThemes\s*=\s*\[)([^\]]*?)(\])",
    re.DOTALL,
)


# ---------------------------------------------------------------------------
# Tool class
# ---------------------------------------------------------------------------

class ThemeAuthor(Tool):
    """
    Deploy, validate, list, or remove Agent Zero webUI themes.
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

    # 1. Parse JSON
    try:
        theme = json.loads(theme_json_str)
    except json.JSONDecodeError as e:
        return [f"Invalid JSON: {e}"]

    if not isinstance(theme, dict):
        return ["Theme must be a JSON object."]

    # 2. Required top-level fields
    missing = REQUIRED_TOP_FIELDS - set(theme.keys())
    for f in sorted(missing):
        errors.append(f"Missing required field: {f}")

    # 3. Required color keys
    colors = theme.get("colors", {})
    if isinstance(colors, dict):
        missing_colors = REQUIRED_COLOR_KEYS - set(colors.keys())
        for k in sorted(missing_colors):
            errors.append(f"Missing required color key: colors.{k}")

        # 4. Validate each color value format
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

    # 5. Tier validation (optional field)
    tier = theme.get("tier")
    if tier is not None and tier not in VALID_TIERS:
        errors.append(
            f"Invalid tier: {tier!r}. Must be one of: {', '.join(sorted(VALID_TIERS))}"
        )

    return errors


def _deploy(theme_key: str, theme_json_str: str) -> str:
    """Validate, write theme file, update theme-store.js. Returns status message."""
    # Validate key format
    if not re.match(r'^[a-z0-9][a-z0-9-]*$', theme_key):
        return (
            f"[THEME] Error: invalid theme_key '{theme_key}'. "
            "Use lowercase letters, digits, and hyphens only."
        )

    # Validate JSON
    errors = _validate(theme_json_str)
    if errors:
        return "[THEME] Validation failed — not deployed:\n" + "\n".join(
            f"  - {e}" for e in errors
        )

    theme = json.loads(theme_json_str)
    theme_name = theme.get("name", theme_key)

    # Write theme JSON
    dest_path = os.path.join(THEMES_DIR, f"{theme_key}.json")
    try:
        with open(dest_path, "w", encoding="utf-8") as f:
            json.dump(theme, f, indent=2, ensure_ascii=False)
    except OSError as e:
        return f"[THEME] Error writing theme file: {e}"

    # Update theme-store.js
    store_result = _add_to_known_themes(theme_key)

    return (
        f"[THEME] Deployed '{theme_name}' as key '{theme_key}'.\n"
        f"  File: {dest_path}\n"
        f"  Store: {store_result}"
    )


def _remove_theme(theme_key: str) -> str:
    """Delete theme JSON and remove from knownThemes."""
    theme_path = os.path.join(THEMES_DIR, f"{theme_key}.json")

    removed_file = False
    if os.path.exists(theme_path):
        try:
            os.remove(theme_path)
            removed_file = True
        except OSError as e:
            return f"[THEME] Error deleting theme file: {e}"
    else:
        pass  # May still be in knownThemes; remove it anyway

    store_result = _remove_from_known_themes(theme_key)

    if removed_file:
        return f"[THEME] Removed theme '{theme_key}'.\n  Store: {store_result}"
    else:
        return (
            f"[THEME] Theme file '{theme_key}.json' not found "
            f"(may already be deleted).\n  Store: {store_result}"
        )


def _list_themes() -> str:
    """List all theme JSON files with name and tier."""
    try:
        entries = []
        for fname in sorted(os.listdir(THEMES_DIR)):
            if not fname.endswith(".json") or fname == "template.json":
                continue
            key = fname[:-5]
            try:
                with open(os.path.join(THEMES_DIR, fname), encoding="utf-8") as f:
                    data = json.load(f)
                name = data.get("name", key)
                tier = data.get("tier", "palette")
                entries.append(f"  {key:<20}  {name:<22}  tier={tier}")
            except Exception as e:
                entries.append(f"  {key:<20}  (error reading: {e})")

        if not entries:
            return "[THEME] No themes installed."
        return "[THEME] Installed themes:\n" + "\n".join(entries)
    except Exception as e:
        return f"[THEME] Error listing themes: {e}"


# ---------------------------------------------------------------------------
# theme-store.js helpers
# ---------------------------------------------------------------------------

def _add_to_known_themes(theme_key: str) -> str:
    """Add theme_key to knownThemes array if not present. Returns status string."""
    try:
        with open(THEME_STORE_PATH, encoding="utf-8") as f:
            content = f.read()
    except OSError as e:
        return f"could not read theme-store.js: {e}"

    m = KNOWN_THEMES_RE.search(content)
    if not m:
        return "knownThemes array not found in theme-store.js — manual update required"

    keys_str = m.group(2)
    # Parse existing keys
    existing = [k.strip().strip("'\"") for k in keys_str.split(",") if k.strip()]

    if theme_key in existing:
        return "already in knownThemes (no change)"

    existing.append(theme_key)
    new_keys_str = ", ".join(f"'{k}'" for k in existing)
    new_content = content[: m.start(2)] + new_keys_str + content[m.end(2):]

    try:
        with open(THEME_STORE_PATH, "w", encoding="utf-8") as f:
            f.write(new_content)
        return f"added '{theme_key}' to knownThemes"
    except OSError as e:
        return f"could not write theme-store.js: {e}"


def _remove_from_known_themes(theme_key: str) -> str:
    """Remove theme_key from knownThemes array. Returns status string."""
    try:
        with open(THEME_STORE_PATH, encoding="utf-8") as f:
            content = f.read()
    except OSError as e:
        return f"could not read theme-store.js: {e}"

    m = KNOWN_THEMES_RE.search(content)
    if not m:
        return "knownThemes array not found in theme-store.js — manual update required"

    keys_str = m.group(2)
    existing = [k.strip().strip("'\"") for k in keys_str.split(",") if k.strip()]

    if theme_key not in existing:
        return f"'{theme_key}' not found in knownThemes (no change)"

    existing = [k for k in existing if k != theme_key]
    new_keys_str = ", ".join(f"'{k}'" for k in existing)
    new_content = content[: m.start(2)] + new_keys_str + content[m.end(2):]

    try:
        with open(THEME_STORE_PATH, "w", encoding="utf-8") as f:
            f.write(new_content)
        return f"removed '{theme_key}' from knownThemes"
    except OSError as e:
        return f"could not write theme-store.js: {e}"
