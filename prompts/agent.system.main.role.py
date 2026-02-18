import os
import json
from typing import Any
from python.helpers.files import VariablesPlugin
from python.helpers import settings


class PersonalityLoader(VariablesPlugin):
    """Loads active AIEOS personality JSON and extracts prompt-ready text."""

    PERSONALITIES_DIR = "/a0/usr/personalities"
    FALLBACK_PERSONALITY = ""

    def get_variables(
        self, file: str, backup_dirs: list[str] | None = None, **kwargs
    ) -> dict[str, Any]:
        try:
            active = self._get_active_personality()
            if not active:
                return {"personality": self.FALLBACK_PERSONALITY}

            persona_text = self._extract_prompt_text(active)
            return {"personality": persona_text}
        except Exception:
            return {"personality": self.FALLBACK_PERSONALITY}

    def _get_active_personality(self) -> dict | None:
        """Find and load the active personality JSON."""
        personalities_dir = self.PERSONALITIES_DIR

        if not os.path.isdir(personalities_dir):
            return None

        # Check settings for explicit personality selection
        s = settings.get_settings()
        selected = s.get("personality_file", "")

        if selected:
            path = os.path.join(personalities_dir, selected)
            if os.path.isfile(path):
                return self._load_json(path)

        # Fallback: look for _active.json
        active_path = os.path.join(personalities_dir, "_active.json")
        if os.path.isfile(active_path):
            return self._load_json(active_path)

        # Fallback: load first .json file alphabetically
        files = sorted(
            f for f in os.listdir(personalities_dir)
            if f.endswith(".json") and not f.startswith(".")
        )
        if files:
            return self._load_json(os.path.join(personalities_dir, files[0]))

        return None

    def _load_json(self, path: str) -> dict | None:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def _extract_prompt_text(self, data: dict) -> str:
        """Distill AIEOS JSON into focused personality prompt text."""
        sections = []

        # Identity
        identity = data.get("identity", {})
        names = identity.get("names", {})
        name = names.get("nickname") or names.get("first", "")
        if name:
            sections.append(f"You are {name}.")

        bio = identity.get("bio", {})
        origin = identity.get("origin", {})
        if origin.get("nationality"):
            age_str = f", age {bio['age_perceived']}" if bio.get("age_perceived") else ""
            sections.append(
                f"Nationality: {origin['nationality']}{age_str}."
            )

        # Occupation
        history = data.get("history", {})
        occupation = history.get("occupation", {})
        if occupation.get("title"):
            sections.append(f"Role: {occupation['title']}.")

        # Core drive
        motivations = data.get("motivations", {})
        core_drive = motivations.get("core_drive", "")
        if core_drive:
            # Truncate to first 200 chars to save tokens
            drive_text = core_drive.strip()[:200]
            if len(core_drive.strip()) > 200:
                drive_text += "..."
            sections.append(f"Core drive: {drive_text}")

        # Linguistics - this is the most important section for voice
        linguistics = data.get("linguistics", {})
        text_style = linguistics.get("text_style", {})
        syntax = linguistics.get("syntax", {})
        interaction = linguistics.get("interaction", {})
        idiolect = linguistics.get("idiolect", {})

        style_parts = []
        if text_style.get("style_descriptors"):
            style_parts.append(
                "Communication style: " + ", ".join(text_style["style_descriptors"])
            )
        if text_style.get("formality_level"):
            level = text_style["formality_level"]
            if level > 0.7:
                style_parts.append("Highly formal register.")
            elif level < 0.3:
                style_parts.append("Casual register.")
        if text_style.get("verbosity_level") is not None:
            v = text_style["verbosity_level"]
            if v < 0.2:
                style_parts.append("Extremely concise.")
            elif v > 0.7:
                style_parts.append("Verbose and detailed.")
        if syntax.get("sentence_structure"):
            style_parts.append(f"Sentence structure: {syntax['sentence_structure']}.")
        if interaction.get("emotional_coloring"):
            style_parts.append(f"Tone: {interaction['emotional_coloring']}.")
        if style_parts:
            sections.append(" ".join(style_parts))

        # Catchphrases
        if idiolect.get("catchphrases"):
            phrases = idiolect["catchphrases"][:4]  # Max 4
            sections.append(
                "Signature phrases: " + " | ".join(f'"{p}"' for p in phrases)
            )

        # Forbidden words
        if idiolect.get("forbidden_words"):
            sections.append(
                "Never use these words: " + ", ".join(idiolect["forbidden_words"])
            )

        # Psychology - light touch, just traits that affect communication
        psychology = data.get("psychology", {})
        neural = psychology.get("neural_matrix", {})
        if neural:
            high_traits = [
                k for k, v in neural.items()
                if isinstance(v, (int, float)) and v > 0.75 and k != "@type"
            ]
            if high_traits:
                sections.append(f"Dominant traits: {', '.join(high_traits)}.")

        # Interests - just favorites for flavor
        interests = data.get("interests", {})
        favorites = interests.get("favorites", {})
        aversions = interests.get("aversions", [])
        if favorites.get("food") or favorites.get("book"):
            fav_items = []
            for key in ["book", "movie", "food"]:
                if favorites.get(key):
                    fav_items.append(f"{key}: {favorites[key]}")
            if fav_items:
                sections.append("Favorites: " + ", ".join(fav_items))
        if aversions:
            sections.append("Dislikes: " + ", ".join(aversions[:3]))

        return "\n".join(sections)
