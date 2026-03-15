"""
success_profile_store.py — Exocortex Behavioral Success Profiles

Phase 3 of the Adaptive Supervisor. Symmetric to the anti-pattern system
(Tier 4) but captures what productive work looks like rather than failure.

Stores per-tool-per-domain distributions of failures_before_success,
derived from episode-level observations captured at task resolution.
The supervisor queries this store to replace static DOMAIN_THRESHOLDS
with learned values when sufficient observations exist.

Three-layer threshold priority (in supervisor):
  1. Learned profile (observation_count >= MIN_OBSERVATIONS_FOR_LEARNING): use p50/p90
  2. Static DOMAIN_THRESHOLDS: per-domain hand-tuned values
  3. Default 3/6/9: cold start prior (safety floors ensure learned never goes below)

Key: (tool_name, primary_domain) — compound domains decompose to primary for keying.
Observation window: bounded list of 20 failures_before_success values.
p50/p90 computed on query from the bounded list (transparent, inspectable).

Location: /a0/usr/Exocortex/success_profile_store.py
Used by: _50_supervisor_loop.py (write from episode buffer, read at threshold selection)
Populated by: _30_tool_fallback_logger.py (buffers success episodes before counter reset)
"""

import os
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


PROFILE_STORE_PATH = "/a0/usr/Exocortex/success_profiles.json"
MAX_OBSERVATIONS = 20
MIN_OBSERVATIONS_FOR_LEARNING = 3


@dataclass
class SuccessProfile:
    """
    Quantitative description of what productive work looks like for a
    given (tool_name, primary_domain) pair.

    The key fields for threshold selection: p50 and p90, computed from
    the bounded observation list.
      - p50 → tier1 threshold (first warning)
      - p90 → tier2 threshold (context surgery)
      - p90 * 1.5 → tier3 threshold (circuit breaker)

    Safety floors: learned values never go below the cold-start defaults (3/6/9).
    """
    tool_name: str
    domain: str
    observations: list = field(default_factory=list)  # list[int]: failures_before_success
    max_observations: int = MAX_OBSERVATIONS
    observation_count: int = 0
    last_updated: str = ""
    compound_domains_seen: list = field(default_factory=list)

    @property
    def p50(self) -> float:
        """Median failures_before_success — used as tier1 threshold."""
        if not self.observations:
            return 0.0
        sorted_obs = sorted(self.observations)
        return float(sorted_obs[len(sorted_obs) // 2])

    @property
    def p90(self) -> float:
        """90th percentile failures_before_success — used as tier2 threshold."""
        if not self.observations:
            return 0.0
        sorted_obs = sorted(self.observations)
        idx = int(len(sorted_obs) * 0.9)
        return float(sorted_obs[min(idx, len(sorted_obs) - 1)])

    def add_observation(self, failures_before_success: int, compound_domain: str = ""):
        """
        Add a new failures_before_success datapoint from a resolved episode.
        Maintains bounded window — oldest observation drops when window is full.
        """
        self.observations.append(int(failures_before_success))
        if len(self.observations) > self.max_observations:
            self.observations.pop(0)
        self.observation_count += 1
        self.last_updated = datetime.now(timezone.utc).isoformat()
        if compound_domain and compound_domain not in self.compound_domains_seen:
            self.compound_domains_seen.append(compound_domain)

    def to_dict(self) -> dict:
        return {
            "tool_name": self.tool_name,
            "domain": self.domain,
            "observations": self.observations,
            "max_observations": self.max_observations,
            "observation_count": self.observation_count,
            "last_updated": self.last_updated,
            "compound_domains_seen": self.compound_domains_seen,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SuccessProfile":
        return cls(
            tool_name=d.get("tool_name", ""),
            domain=d.get("domain", ""),
            observations=d.get("observations", []),
            max_observations=d.get("max_observations", MAX_OBSERVATIONS),
            observation_count=d.get("observation_count", 0),
            last_updated=d.get("last_updated", ""),
            compound_domains_seen=d.get("compound_domains_seen", []),
        )


class ProfileStore:
    """
    In-memory cache of SuccessProfile records, backed by JSON on disk.

    Load: on first access (lazy) or explicit _load() call.
    Flush: after each new observation batch (deferred writes).
    Key: (tool_name, primary_domain) — one profile per tool per domain.

    Thread safety: not required — Agent Zero runs single-threaded.
    """

    def __init__(self, path: str = PROFILE_STORE_PATH):
        self.path = path
        self.profiles: dict = {}  # (tool_name, domain) -> SuccessProfile
        self._dirty = False
        self._loaded = False
        self._load()

    def get(self, tool_name: str, domain: str) -> Optional[SuccessProfile]:
        """Get profile for (tool_name, primary_domain). Returns None if not found."""
        if not self._loaded:
            self._load()
        return self.profiles.get((tool_name, domain))

    def get_for_compound(self, tool_name: str, compound_domain: str) -> Optional[SuccessProfile]:
        """
        Get the most permissive profile for a compound domain (e.g. "codegen+debugging").

        Decomposes the compound to primary domains and returns the candidate with
        the highest p90 (most permissive = highest ceiling before concern).
        Only returns profiles that have reached MIN_OBSERVATIONS_FOR_LEARNING.
        Returns None to fall back to static thresholds when no qualifying profile exists.
        """
        if not self._loaded:
            self._load()
        if not compound_domain or "+" not in compound_domain:
            return self.get(tool_name, compound_domain or "")
        domains = compound_domain.split("+")
        candidates = [self.get(tool_name, d.strip()) for d in domains]
        candidates = [
            c for c in candidates
            if c is not None and c.observation_count >= MIN_OBSERVATIONS_FOR_LEARNING
        ]
        if not candidates:
            return None
        # Most permissive = highest p90 (widest tolerance ceiling)
        return max(candidates, key=lambda p: p.p90)

    def put(self, profile: SuccessProfile):
        """Store or update a profile. Marks store dirty for flush."""
        self.profiles[(profile.tool_name, profile.domain)] = profile
        self._dirty = True

    def get_or_create(self, tool_name: str, domain: str) -> SuccessProfile:
        """Get existing profile or create a new empty one (not yet persisted)."""
        existing = self.get(tool_name, domain)
        if existing is not None:
            return existing
        return SuccessProfile(tool_name=tool_name, domain=domain)

    def record_episode(self, tool_name: str, failures_before_success: int,
                       compound_domain: str = "") -> SuccessProfile:
        """
        Add a new observation to the profile for (tool_name, primary_domain).
        Decomposes compound_domain to primary domain for key. Creates new profile
        if one doesn't exist yet. Returns the updated profile.
        """
        primary_domain = compound_domain.split("+")[0].strip() if compound_domain else ""
        profile = self.get_or_create(tool_name, primary_domain)
        profile.add_observation(failures_before_success, compound_domain)
        self.put(profile)
        return profile

    def flush(self):
        """Write all profiles to disk if dirty. Atomic write via .tmp rename."""
        if not self._dirty:
            return
        try:
            data = {
                f"{k[0]}|{k[1]}": v.to_dict()
                for k, v in self.profiles.items()
            }
            dir_path = os.path.dirname(self.path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            tmp_path = self.path + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp_path, self.path)  # atomic
            self._dirty = False
        except Exception:
            pass  # graceful degradation — learning is best-effort, never crashes

    def _load(self):
        """Load profiles from disk. Graceful on missing or corrupt file."""
        self._loaded = True
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for key_str, profile_dict in data.items():
                parts = key_str.split("|", 1)
                if len(parts) == 2:
                    tool_name, domain = parts
                    profile = SuccessProfile.from_dict(profile_dict)
                    self.profiles[(tool_name, domain)] = profile
        except Exception:
            pass  # corrupt or empty — start fresh

    def summary(self) -> dict:
        """Return a summary dict for stack_status tool reporting."""
        return {
            "profile_count": len(self.profiles),
            "profiles": [
                {
                    "tool": k[0],
                    "domain": k[1],
                    "n": v.observation_count,
                    "p50": round(v.p50, 1),
                    "p90": round(v.p90, 1),
                }
                for k, v in sorted(self.profiles.items())
            ],
        }
