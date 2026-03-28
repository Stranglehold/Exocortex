#!/usr/bin/env python3
"""
Theme JSON Validator for the Aesthetic Theme Engine.
Usage: python validate_theme.py themes/yorha.json

Validates a theme file against the full schema. Exit code 0 on pass, 1 on fail.
No LLM calls. Deterministic validation only.
"""

import json
import re
import sys
import os
from pathlib import Path

# ── Constants ─────────────────────────────────────────────────────────────────

REQUIRED_TOP_LEVEL = ['name', 'author', 'description', 'version', 'colors', 'fonts', 'preview']

REQUIRED_COLOR_KEYS = [
    'background', 'text', 'text-muted', 'primary', 'secondary', 'accent',
    'message-bg', 'highlight', 'message-text', 'panel', 'border',
    'input', 'input-focus', 'chat-background', 'error-text', 'warning-text', 'table-row'
]

REQUIRED_FONT_KEYS = ['main', 'code']
REQUIRED_PREVIEW_KEYS = ['background', 'text', 'accent']
VALID_TIERS = ['palette', 'atmospheric', 'immersive']
VALID_ANIMATION_TYPES = ['none', 'rain', 'snow', 'particles', 'static']
VALID_BG_TYPES = ['none', 'image']

# Hex color: #rgb, #rrggbb, #rrggbbaa
HEX_RE = re.compile(r'^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$')
# rgba(r, g, b, a) or rgb(r, g, b)
RGBA_RE = re.compile(r'^rgba?\(\s*\d+\s*,\s*\d+\s*,\s*\d+(\s*,\s*[\d.]+)?\s*\)$')


# ── Helpers ───────────────────────────────────────────────────────────────────

def is_valid_color(value):
    if not isinstance(value, str):
        return False
    return bool(HEX_RE.match(value)) or bool(RGBA_RE.match(value))


def check_range(value, name, lo, hi, errors):
    if not isinstance(value, (int, float)):
        errors.append(f"  {name}: expected number, got {type(value).__name__}")
        return
    if value < lo or value > hi:
        errors.append(f"  {name}: {value} out of range [{lo}, {hi}]")


def resolve_asset_path(src, theme_file_path):
    """
    Given a src like '/themes/assets/foo.svg', resolve to the repo patch path.
    Base: the directory two levels up from the theme file (repo root),
    then patches/webui + src.
    """
    # Try relative to repo: patches/webui/themes/assets/...
    theme_path = Path(theme_file_path).resolve()
    # Walk up to find repo root (contains patches/ directory)
    candidate = theme_path.parent
    for _ in range(6):
        if (candidate / 'patches').exists():
            return candidate / 'patches' / 'webui' / src.lstrip('/')
        candidate = candidate.parent
    # Fallback: relative to theme file's parent
    return theme_path.parent / src.lstrip('/')


# ── Tier Inference ────────────────────────────────────────────────────────────

def infer_tier(data):
    """
    Infer what tier this theme actually uses based on populated fields.
    palette: no background/overlay/animation non-defaults
    atmospheric: background image OR overlay effects, no animation
    immersive: animation type != none
    """
    anim = data.get('animation', {})
    if anim.get('type', 'none') not in ('none', None):
        return 'immersive'

    bg = data.get('background', {})
    overlay = data.get('overlay', {})
    has_bg = bg.get('src') is not None and bg.get('type', 'none') != 'none'

    has_overlay = any([
        overlay.get('scanlines', {}).get('enabled', False),
        overlay.get('vignette', {}).get('enabled', False),
        overlay.get('noise', {}).get('enabled', False),
        overlay.get('watermark', {}).get('enabled', False),
    ])

    panel = data.get('panel', {})
    has_panel_fx = panel.get('opacity', 1.0) < 1.0 or panel.get('backdrop_blur', 0) > 0

    if has_bg or has_overlay or has_panel_fx:
        return 'atmospheric'

    return 'palette'


# ── Main Validator ────────────────────────────────────────────────────────────

def validate(theme_file):
    errors = []
    warnings = []

    # Load file
    try:
        with open(theme_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"FAIL: File not found: {theme_file}")
        return 1
    except json.JSONDecodeError as e:
        print(f"FAIL: Invalid JSON: {e}")
        return 1

    theme_name = data.get('name', theme_file)

    # ── Required top-level fields ──────────────────────────────────────────
    for field in REQUIRED_TOP_LEVEL:
        if field not in data:
            errors.append(f"  Missing required field: '{field}'")

    # ── Tier ──────────────────────────────────────────────────────────────
    tier = data.get('tier', None)
    if tier is not None and tier not in VALID_TIERS:
        errors.append(f"  tier: '{tier}' is not valid. Must be one of: {VALID_TIERS}")

    inferred = infer_tier(data)
    if tier and tier != inferred:
        warnings.append(f"  tier: declared '{tier}' but inferred '{inferred}' from field usage")

    # ── Colors ────────────────────────────────────────────────────────────
    colors = data.get('colors', {})
    if isinstance(colors, dict):
        for key in REQUIRED_COLOR_KEYS:
            if key not in colors:
                errors.append(f"  colors.{key}: missing required color key")
            elif not is_valid_color(colors[key]):
                errors.append(f"  colors.{key}: '{colors[key]}' is not a valid hex or rgba color")
    else:
        errors.append("  'colors' must be an object")

    # ── Fonts ─────────────────────────────────────────────────────────────
    fonts = data.get('fonts', {})
    if isinstance(fonts, dict):
        for key in REQUIRED_FONT_KEYS:
            if key not in fonts:
                errors.append(f"  fonts.{key}: missing required font key")
            elif not isinstance(fonts[key], str) or not fonts[key].strip():
                errors.append(f"  fonts.{key}: must be a non-empty string")
    else:
        errors.append("  'fonts' must be an object")

    # ── Preview ───────────────────────────────────────────────────────────
    preview = data.get('preview', {})
    if isinstance(preview, dict):
        for key in REQUIRED_PREVIEW_KEYS:
            if key not in preview:
                errors.append(f"  preview.{key}: missing required preview key")
            elif not is_valid_color(preview[key]):
                errors.append(f"  preview.{key}: '{preview[key]}' is not a valid color")
    else:
        errors.append("  'preview' must be an object")

    # ── Background ────────────────────────────────────────────────────────
    bg = data.get('background', None)
    if bg is not None:
        if not isinstance(bg, dict):
            errors.append("  'background' must be an object")
        else:
            bg_type = bg.get('type', 'none')
            if bg_type not in VALID_BG_TYPES:
                errors.append(f"  background.type: '{bg_type}' not valid. Use 'none' or 'image'")

            if 'opacity' in bg:
                check_range(bg['opacity'], 'background.opacity', 0.0, 1.0, errors)
            if 'blur' in bg:
                if not isinstance(bg['blur'], (int, float)) or bg['blur'] < 0:
                    errors.append(f"  background.blur: {bg['blur']} must be >= 0")

            # Check asset path if src is set
            if bg.get('src') is not None:
                asset_path = resolve_asset_path(bg['src'], theme_file)
                if not asset_path.exists():
                    warnings.append(f"  background.src: asset not found at {asset_path}")

    # ── Panel ─────────────────────────────────────────────────────────────
    panel = data.get('panel', None)
    if panel is not None:
        if not isinstance(panel, dict):
            errors.append("  'panel' must be an object")
        else:
            if 'opacity' in panel:
                check_range(panel['opacity'], 'panel.opacity', 0.0, 1.0, errors)
            if 'backdrop_blur' in panel:
                if not isinstance(panel['backdrop_blur'], (int, float)) or panel['backdrop_blur'] < 0:
                    errors.append(f"  panel.backdrop_blur: {panel['backdrop_blur']} must be >= 0")

    # ── Overlay ───────────────────────────────────────────────────────────
    overlay = data.get('overlay', None)
    if overlay is not None:
        if not isinstance(overlay, dict):
            errors.append("  'overlay' must be an object")
        else:
            # Scanlines
            sl = overlay.get('scanlines', {})
            if isinstance(sl, dict):
                if 'opacity' in sl:
                    check_range(sl['opacity'], 'overlay.scanlines.opacity', 0.0, 1.0, errors)
                if 'spacing' in sl:
                    if not isinstance(sl['spacing'], (int, float)) or sl['spacing'] < 1:
                        errors.append(f"  overlay.scanlines.spacing: {sl['spacing']} must be >= 1")

            # Vignette
            vig = overlay.get('vignette', {})
            if isinstance(vig, dict) and 'opacity' in vig:
                check_range(vig['opacity'], 'overlay.vignette.opacity', 0.0, 1.0, errors)

            # Noise
            noise = overlay.get('noise', {})
            if isinstance(noise, dict) and 'opacity' in noise:
                check_range(noise['opacity'], 'overlay.noise.opacity', 0.0, 1.0, errors)

            # Watermark
            wm = overlay.get('watermark', {})
            if isinstance(wm, dict):
                if 'opacity' in wm:
                    check_range(wm['opacity'], 'overlay.watermark.opacity', 0.0, 1.0, errors)
                if wm.get('enabled', False) and wm.get('src') is not None:
                    asset_path = resolve_asset_path(wm['src'], theme_file)
                    if not asset_path.exists():
                        warnings.append(f"  overlay.watermark.src: asset not found at {asset_path}")

    # ── Animation ─────────────────────────────────────────────────────────
    anim = data.get('animation', None)
    if anim is not None:
        if not isinstance(anim, dict):
            errors.append("  'animation' must be an object")
        else:
            anim_type = anim.get('type', 'none')
            if anim_type not in VALID_ANIMATION_TYPES:
                errors.append(f"  animation.type: '{anim_type}' not valid. Must be one of: {VALID_ANIMATION_TYPES}")
            if 'intensity' in anim:
                check_range(anim['intensity'], 'animation.intensity', 0.0, 5.0, errors)
            if 'color' in anim and anim['color'] is not None:
                if not is_valid_color(anim['color']):
                    errors.append(f"  animation.color: '{anim['color']}' is not a valid color")

    # ── Report ─────────────────────────────────────────────────────────────
    print(f"\nValidating: {theme_file}")
    print(f"Theme: {theme_name}")
    print(f"Declared tier: {tier or '(not set)'} | Inferred tier: {inferred}")
    print()

    if warnings:
        print("WARNINGS:")
        for w in warnings:
            print(w)
        print()

    if errors:
        print(f"FAIL — {len(errors)} error(s):")
        for e in errors:
            print(e)
        return 1
    else:
        color_count = len([k for k in colors if isinstance(colors, dict)])
        print(f"PASS — {theme_name} ({tier or inferred}) — {len(colors)} colors, {len(warnings)} warning(s)")
        return 0


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python validate_theme.py <theme.json>")
        print("Example: python validate_theme.py themes/yorha.json")
        sys.exit(1)

    theme_file = sys.argv[1]
    sys.exit(validate(theme_file))
