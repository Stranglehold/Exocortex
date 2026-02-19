"""
Model Profile Loader — Shared utility for hardening extensions.
================================================================
Each extension calls get_section() to load its configuration section
from the active model profile. Falls back to defaults if no profile exists.

Deploy this file to: /a0/python/extensions/before_main_llm_call/model_profile_loader.py

Usage in extensions:
    from model_profile_loader import get_section

    profile = get_section("bst")
    confidence_adj = profile.get("confidence_adjustment", 0)
    disabled_domains = profile.get("disabled_domains", [])
"""

import json
from pathlib import Path

PROFILE_DIR = Path("/a0/usr/model_profiles")
DEFAULT_PROFILE = PROFILE_DIR / "default.json"
_cached_profile = None


def load_profile(model_name: str = None) -> dict:
    """Load the active model profile.

    Resolution order:
      1. Model-specific profile: /a0/usr/model_profiles/<model_name>.json
      2. Default profile: /a0/usr/model_profiles/default.json
      3. Empty dict (extensions use their hardcoded defaults)
    """
    global _cached_profile
    if _cached_profile is not None:
        return _cached_profile

    # Try model-specific profile
    if model_name:
        specific = PROFILE_DIR / f"{model_name}.json"
        if specific.exists():
            try:
                with open(specific, "r", encoding="utf-8") as f:
                    _cached_profile = json.load(f)
                return _cached_profile
            except Exception:
                pass

    # Try default profile
    if DEFAULT_PROFILE.exists():
        try:
            with open(DEFAULT_PROFILE, "r", encoding="utf-8") as f:
                _cached_profile = json.load(f)
            return _cached_profile
        except Exception:
            pass

    # Return empty dict — each extension uses its own hardcoded defaults
    _cached_profile = {}
    return _cached_profile


def get_section(section_name: str, model_name: str = None) -> dict:
    """Get a specific section from the model profile.

    Args:
        section_name: Profile section key (e.g. "bst", "meta_gate", "pace")
        model_name: Optional model name for model-specific profile lookup

    Returns:
        Dict of configuration values for that section, or empty dict.
    """
    profile = load_profile(model_name)
    return profile.get(section_name, {})


def invalidate_cache():
    """Clear the cached profile (e.g., after profile update)."""
    global _cached_profile
    _cached_profile = None
