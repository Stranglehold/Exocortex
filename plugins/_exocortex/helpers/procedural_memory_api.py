"""
procedural_memory_api.py — Exocortex Procedural Memory

Manages procedural (how-to) knowledge separate from declarative (what-is) facts.
Stores skill files as markdown + .index.json for deterministic tag-based retrieval.

Location: /a0/usr/plugins/_exocortex/helpers/procedural_memory_api.py
Used by: _50_supervisor_loop.py (write on loop recovery) and
         _11_belief_state_tracker.py (read at task start for anti-pattern injection)
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional


class ProceduralMemory:
    """Manages procedural (how-to) knowledge separate from declarative (what-is) facts."""

    def __init__(self, base_path: str = '/a0/usr/Exocortex/procedural_memory'):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)
        self.index_file = os.path.join(base_path, '.index.json')
        self._load_index()

    def _load_index(self):
        """Load the skills index from disk."""
        if os.path.exists(self.index_file):
            with open(self.index_file, 'r') as f:
                self.index = json.load(f)
        else:
            self.index = {"skills": [], "metadata": {}}

    def _save_index(self):
        """Save the skills index to disk."""
        with open(self.index_file, 'w') as f:
            json.dump(self.index, f, indent=2)

    def create_skill_from_experience(
        self,
        skill_name: str,
        problem_pattern: str,
        solution_approach: str,
        key_steps: List[str],
        verification_method: str = "",
        related_facts: List[str] = None,
        tags: List[str] = None
    ) -> str:
        """
        Create a new procedural skill from problem-solving experience.

        Returns:
            Path to created skill file
        """
        timestamp = datetime.now().isoformat()
        session_id = os.environ.get('A0_CHAT_ID', 'unknown')

        # Generate unique filename — keep alphanumeric and hyphens, replace rest with underscores
        safe_name = ''.join([c.lower() if c.isalnum() or c in '-' else '_' for c in skill_name])
        filename = f"{safe_name}_{timestamp}.md"
        filepath = os.path.join(self.base_path, filename)

        content = f"# Procedural Skill: {skill_name}\n\n"
        content += f"## Type: PROCEDURAL (How-To Knowledge)\n"
        content += f"Created: {timestamp}\n"
        content += f"Source Session: {session_id}\n"
        content += f"Tags: {', '.join(tags) if tags else 'general'}\n\n---\n\n"
        content += f"## Problem Pattern Recognized\n{problem_pattern}\n\n"
        content += f"## Solution Approach Discovered\n{solution_approach}\n\n"
        content += "## Key Steps/Methodology\n"
        for i, step in enumerate(key_steps, 1):
            content += f"{i}. {step}\n"

        if verification_method:
            content += f"\n## Verification Method\n{verification_method}\n"

        if related_facts:
            content += "\n## Related Declarative Knowledge (Facts)\n"
            for fact in related_facts:
                content += f"- {fact}\n"

        content += "\n---\n*Auto-generated from session experience. Edit to refine.*\n"

        with open(filepath, 'w') as f:
            f.write(content)

        skill_entry = {
            "name": skill_name,
            "type": "PROCEDURAL",
            "filepath": filepath,
            "created": timestamp,
            "session_id": session_id,
            "tags": tags or [],
            "problem_pattern_hash": hashlib.md5(problem_pattern.encode()).hexdigest()[:8]
        }
        self.index["skills"].append(skill_entry)
        self._save_index()

        return filepath


    def create_anti_pattern(
        self,
        failing_tool: str,
        domain: str,
        consecutive: int,
        pre_action_check: str,
        session_id: str = None,
        tags: List[str] = None
    ) -> str:
        """
        Create an anti-pattern entry from loop recovery data.
        Anti-patterns are what NOT to do — captured after loop resolution
        so the same pattern can be prevented in future sessions.

        Args:
            failing_tool: Tool that caused the loop (e.g., "document_query")
            domain: BST domain at time of loop (e.g., "investigation")
            consecutive: How many consecutive failures before recovery
            pre_action_check: Short instruction for BST injection (1-2 sentences)
            session_id: Source session ID (uses env var if not provided)
            tags: Additional tags beyond failing_tool and domain

        Returns:
            Path to created anti-pattern file
        """
        timestamp = datetime.now().isoformat()
        sid = session_id or os.environ.get('A0_CHAT_ID', 'unknown')

        # Build tag list: failing_tool + domain + any extras
        base_tags = [failing_tool, domain, "loop-recovery"]
        all_tags = list(dict.fromkeys(base_tags + (tags or [])))  # deduplicate, preserve order

        # Generate filename
        safe_name = ''.join([c.lower() if c.isalnum() or c in '-' else '_' for c in f"anti_{failing_tool}_{domain}"])
        filename = f"{safe_name}_{timestamp}.md"
        filepath = os.path.join(self.base_path, filename)

        # Problem pattern hash — hash of tool+domain for dedup
        pattern_hash = hashlib.md5(f"{failing_tool}:{domain}".encode()).hexdigest()[:8]

        content = f"# Anti-Pattern: {failing_tool} in {domain}\n\n"
        content += f"## Type: ANTI-PATTERN (What NOT to Do)\n"
        content += f"Created: {timestamp}\n"
        content += f"Source Session: {sid}\n"
        content += f"Tags: {', '.join(all_tags)}\n"
        content += f"Loop Count: {consecutive} repetitions before recovery\n\n---\n\n"
        content += f"## Loop Pattern Recognized\n"
        content += f"Tool '{failing_tool}' failed {consecutive} consecutive times in domain '{domain}'.\n\n"
        content += f"## Pre-Action Check\n{pre_action_check}\n\n"
        content += "---\n*Auto-generated from loop recovery. Edit to refine.*\n"

        with open(filepath, 'w') as f:
            f.write(content)

        entry = {
            "name": f"Anti-Pattern: {failing_tool} in {domain}",
            "type": "ANTI-PATTERN",
            "filepath": filepath,
            "created": timestamp,
            "session_id": sid,
            "tags": all_tags,
            "problem_pattern_hash": pattern_hash,
            "pre_action_check": pre_action_check,   # stored in index for fast retrieval (no file read needed)
            "failing_tool": failing_tool,
            "domain": domain,
            "consecutive": consecutive,
        }
        self.index["skills"].append(entry)
        self._save_index()

        return filepath

    def search_skills(self, query: str, match_type: str = "pattern") -> List[Dict]:
        """
        Search for relevant procedural skills by query string.
        match_type: "pattern" (name similarity) or "tag" (keyword match)
        """
        results = []
        query_lower = query.lower()

        for skill in self.index["skills"]:
            score = 0
            if match_type == "tag":
                for tag in skill.get("tags", []):
                    if query_lower in tag.lower() or tag.lower() in query_lower:
                        score += 10
            if query_lower in skill["name"].lower():
                score += 5
            if score > 0:
                results.append({**skill, "relevance": score})

        return sorted(results, key=lambda x: x["relevance"], reverse=True)

    def search_by_tags(self, tags: List[str], type_filter: str = None) -> List[Dict]:
        """
        Deterministic tag-intersection search. Returns entries that match ALL specified tags.
        Optionally filter by entry type ("PROCEDURAL" or "ANTI-PATTERN").
        Used by BST enrichment phase — no LLM calls, pure index lookup.
        """
        if not tags:
            return []
        tag_set = {t.lower() for t in tags}
        results = []
        for skill in self.index["skills"]:
            if type_filter and skill.get("type", "PROCEDURAL") != type_filter:
                continue
            skill_tags = {t.lower() for t in skill.get("tags", [])}
            if tag_set.issubset(skill_tags):
                results.append(skill)
        return results

    def get_skill(self, filepath: str) -> Optional[str]:
        """Read a skill file by path."""
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return f.read()
        return None

    def list_all_skills(self) -> List[Dict]:
        """Return all indexed skills."""
        return self.index["skills"]
