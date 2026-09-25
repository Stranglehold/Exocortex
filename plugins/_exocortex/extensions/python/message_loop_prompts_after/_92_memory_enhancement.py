"""
Memory Enhancement — Agent-Zero Hardening Layer
=================================================
Hook: message_loop_prompts_after
Priority: _56 (runs AFTER _55_memory_relevance_filter)

Six-stage retrieval pipeline per turn:
  1. Query Expansion: 3 FAISS queries (original, keyword, domain-scoped),
     merged by memory ID keeping highest similarity per document.
  2. Temporal Decay: exponential recency blended with similarity; exempt
     memories (load_bearing, user_asserted, confirmed) bypass decay.
  3. Related Memory Boost: preliminary top-k checked for related IDs;
     linked memories in the broader pool receive a score boost.
  4. Top-K Selection: final cap from model profile or config.
  5. Access Tracking: access_count += 1, last_accessed = utcnow().
  6. Co-Retrieval Logging: append to /a0/usr/memory/co_retrieval_log.json.

Formula:
  recency_score = exp(-decay_rate * age_in_hours)
  decay_rate    = ln(2) / half_life_hours
  final_score   = (1 - decay_weight) * similarity + decay_weight * recency

Reads:
  - query_expansion, temporal_decay, related_memories config sections
  - memory section from active model profile (if available)
  - BST domain classification from agent._bst_store
Writes:
  - loop_data.extras_persistent["memories"], ["solutions"]
  - Document.metadata lineage (access_count, last_accessed)
  - /a0/usr/memory/co_retrieval_log.json
"""

import inspect
import json
import math
import os
import re
import sys
from datetime import datetime, timezone
from typing import Any

from agent import Agent, LoopData
from helpers.extension import Extension
from plugins._memory.helpers.memory import Memory

# The plugin's own helpers are NOT importable as `plugins._exocortex.*`: the plugin lives at
# /a0/usr/plugins/_exocortex/, while `/a0/plugins/` (which is what `import plugins` resolves to)
# holds only A0's core plugins. Verified in her venv 2026-09-17 — `plugins._exocortex` is a
# ModuleNotFoundError there, though it imports fine from the repo tree, which is exactly how a
# package-path import passes a control and then does nothing in production.
#
# So: put the helpers directory on sys.path and import the module by its bare name. Identical to
# _07_recovery_gate.py:100-102 and _10_plaintext_response_fallback.py, which is where this pattern
# already lived while this file failed to use it.
_HELPERS = "/a0/usr/plugins/_exocortex/helpers"
if _HELPERS not in sys.path:
    sys.path.insert(0, _HELPERS)

try:
    import recall_query
except Exception:  # pragma: no cover - helper missing
    recall_query = None  # type: ignore[assignment]

# R3 (memory lifecycle design, Opus 2026-09-23): the recall frame says when a state observation
# is old, and when a newer observation of a subject a memory mentions exists
# (helpers/memory_temporal.py). If the helper cannot load, the frame is the save date alone.
try:
    import memory_temporal as _mt
except Exception:  # pragma: no cover - helper missing
    _mt = None  # type: ignore[assignment]

# Graduated trust, Phase 1 (Opus's note + Kestrel's review, 2026-09-25): whether a recalled memory
# may be presented is decided in helpers/memory_trust.py. If it cannot load, the filter falls back
# to the rule it always applied inline (`validity == "deprecated"`), so recall is unchanged.
try:
    import memory_trust as _trust
except Exception:  # pragma: no cover - helper missing
    _trust = None  # type: ignore[assignment]

# ── Configuration ────────────────────────────────────────────────────────────

CONFIG_PATH = "/a0/usr/memory/classification_config.json"
# Portable across container layouts: plugin (v2) and agent-path/Exocortex (v16/v17).
_PROFILE_DIRS = (
    "/a0/usr/plugins/_exocortex/config/model_profiles",
    "/a0/usr/Exocortex/eval/model_profiles",
)
PROFILE_DIR = next((_d for _d in _PROFILE_DIRS if os.path.isdir(_d)), _PROFILE_DIRS[0])
MODEL_CONFIG_PATH = "/a0/usr/plugins/_model_config/config.json"
CO_RETRIEVAL_LOG = "/a0/usr/memory/co_retrieval_log.json"
MAX_CO_RETRIEVAL_ENTRIES = 500

DEFAULT_CONFIG = {
    "load_bearing_keywords": [
        "must", "always", "never", "requirement", "constraint",
        "critical", "essential", "mandatory", "do not", "required",
    ],
    "max_injected_memories": 8,
}

DEFAULT_QE_CONFIG = {
    "enabled": True,
    "retrieval_k_per_variant": 8,
    "use_domain_scoping": True,
    "use_keyword_extraction": True,
    "max_keywords": 12,
}

DEFAULT_DECAY_CONFIG = {
    "enabled": True,
    "decay_weight": 0.15,
    "half_life_hours": 168,
    "exempt_utilities": ["load_bearing"],
    "exempt_sources": ["user_asserted"],
    "exempt_validities": ["confirmed"],
    "exempt_relational_salience": ["relationship_defining"],
    "collaboration_history_half_life_multiplier": 2.0,
    "min_recency_score": 0.1,
}

DEFAULT_RELATED_CONFIG = {
    "enabled": True,
    "tag_overlap_threshold": 3,
    "related_boost": 0.08,
    "max_related_per_memory": 10,
    "rebuild_interval_cycles": 25,
}

# Metadata keys (must match _55_memory_classifier.py)
CLS_KEY = "classification"
LIN_KEY = "lineage"

# BST access keys (must match _11_belief_state_tracker.py)
BST_STORE_KEY = "_bst_store"
BST_BELIEF_KEY = "__bst_belief_state__"

# Utility rank for sorting (higher = more important)
_UTILITY_ORDER = {"load_bearing": 2, "tactical": 1, "archived": 0}

# Role directory for domain overlap checks
ROLES_DIR = "/a0/usr/organizations/roles"

# ── Stopwords for keyword extraction ─────────────────────────────────────────

STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "shall", "can",
    "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "it", "this", "that", "these", "those", "i", "you", "he",
    "she", "we", "they", "me", "him", "her", "us", "them",
    "my", "your", "his", "its", "our", "their", "and", "or",
    "but", "not", "no", "if", "then", "so", "just", "about",
    "up", "out", "how", "what", "when", "where", "who", "which",
    "there", "here", "all", "each", "some", "any", "into", "as",
}


class MemoryEnhancement(Extension):
    """Six-stage memory retrieval: expand -> decay -> boost -> select -> track -> log."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> Any:
        # Recall trace: exactly ONE row per call, the early returns included, so a turn on which
        # A0's own untagged recall stood (the A17 gap) is a counted row, not an inference.
        turn = getattr(loop_data, "iteration", None)
        traced = False
        try:
            if self.agent.get_data(Agent.DATA_NAME_SUPERIOR) is not None:
                _trace(self.agent, [], turn, early="subordinate")
                return  # subordinate context — skip full memory bootstrap (DEC-028)
            print("[MEM-ENHANCE] execute() called", flush=True)
            if loop_data.extras_persistent is None:
                loop_data.extras_persistent = {}
            extras = loop_data.extras_persistent
            has_solutions = "solutions" in extras

            config = _load_config()
            qe_config = config.get("query_expansion", DEFAULT_QE_CONFIG)
            decay_config = config.get("temporal_decay", DEFAULT_DECAY_CONFIG)
            related_config = config.get("related_memories", DEFAULT_RELATED_CONFIG)

            db = await Memory.get(self.agent)
            if not db or not db.db:
                _trace(self.agent, [], turn, early="no_db")
                return

            all_docs = db.db.get_all_docs()
            if not all_docs:
                _trace(self.agent, [], turn, early="no_docs")
                return

            # R3: each keyed subject's current observation, read once for both frames below.
            observations = {}
            if _mt is not None:
                try:
                    observations = _mt.current_observations(all_docs)
                except Exception:
                    observations = {}

            # ── Load thresholds ───────────────────────────────────────────
            max_injected = config.get("max_injected_memories", 8)
            sim_threshold = 0.3
            try:
                sim_threshold = self.agent.config.memory_recall_similarity_threshold
            except Exception:
                pass

            profile_mem = _load_profile_memory_section()
            if profile_mem:
                max_injected = profile_mem.get("max_injected", max_injected)
                prof_thresh = profile_mem.get("similarity_threshold")
                if prof_thresh is not None and prof_thresh > sim_threshold:
                    sim_threshold = prof_thresh

            # ── Role domains for filtering ────────────────────────────────
            role = getattr(self.agent, "_org_active_role", None)
            role_domains = []
            if role:
                role_domains = role.get("capabilities", {}).get(
                    "bst_domains", []
                )

            # ── BST domain ────────────────────────────────────────────────
            bst_domain = _get_bst_domain(self.agent)

            # ── Maintenance cycle (for co-retrieval logging) ──────────────
            maint_cycle = getattr(
                self.agent, "_memory_maintenance_counter", 0
            )

            query, query_source = _get_query_with_source(self.agent, loop_data, config)
            if not query:
                print("[MEM-ENHANCE] No user message found, skipping", flush=True)
                _trace(self.agent, [], turn, source=query_source, early="no_query")
                return
            print(f"[MEM-ENHANCE] User message: {query[:50]!r}", flush=True)

            all_injected_ids = []
            # A pipeline that raises leaves A0's own text in its slot, untagged: the same gap as an
            # early return, so the trace names it.
            pipeline_errors = []
            # Candidates the trust verdict withheld this turn (helpers/memory_trust.py), for the trace.
            dropped_ids = []
            # Injected ids whose head showed "source: legacy" (GT-2a), for the trace: Fable, 09-25,
            # so "nothing withheld" and "nothing labelled" never read as one zero.
            legacy_ids = []

            # ── Process memories (main + fragments + ontology entities) ───
            try:
                result = await _run_pipeline(
                    db, all_docs, query, bst_domain, role_domains,
                    sim_threshold, max_injected,
                    # Search ALL knowledge areas, not a 4-area whitelist — the agent saves into
                    # ~115 semantic areas (research, field-report, self-improvement, workshop,
                    # [CONCEPT] insights...); the old whitelist orphaned ~32% of memory (write-only).
                    # Similarity threshold + temporal decay are the real quality gates, not the area
                    # bucket. 'solutions' keeps its own targeted path below.
                    "area != 'solutions'",
                    qe_config, decay_config, related_config,
                    dropped=dropped_ids,
                )

                if result:
                    txt = _with_provenance(result, observations, config)
                    try:
                        extras["memories"] = self.agent.parse_prompt(
                            "agent.system.memories.md", memories=txt,
                        )
                    except Exception:
                        extras["memories"] = (
                            f"# Recalled Memories\n\n{txt}"
                        )

                    ids = _update_access(result, all_docs)
                    all_injected_ids.extend(ids)
                    legacy_ids.extend(_legacy_ids(result))
                    print(f"[MEM-ENHANCE] Final selection: {len(ids)} memories injected", flush=True)
                else:
                    extras.pop("memories", None)
                    print("[MEM-ENHANCE] Final selection: 0 memories injected", flush=True)
            except Exception as mem_err:
                print(f"[MEM-ENHANCE] Memories pipeline error: {mem_err}", flush=True)
                pipeline_errors.append("memories")

            # ── Process solutions ─────────────────────────────────────────
            if has_solutions:
                try:
                    sol_cap = max(2, max_injected // 2)
                    result = await _run_pipeline(
                        db, all_docs, query, bst_domain, role_domains,
                        sim_threshold, sol_cap,
                        "area == 'solutions'",
                        qe_config, decay_config, related_config,
                        dropped=dropped_ids,
                    )

                    if result:
                        txt = _with_provenance(result, observations, config)
                        try:
                            extras["solutions"] = self.agent.parse_prompt(
                                "agent.system.solutions.md", solutions=txt,
                            )
                        except Exception:
                            extras["solutions"] = (
                                f"# Recalled Solutions\n\n{txt}"
                            )

                        ids = _update_access(result, all_docs)
                        all_injected_ids.extend(ids)
                        legacy_ids.extend(_legacy_ids(result))
                    else:
                        del extras["solutions"]
                except Exception:
                    pipeline_errors.append("solutions")

            # ── Persist access updates ────────────────────────────────────
            if all_injected_ids:
                try:
                    db._save_db()
                except Exception:
                    pass

            # ── Recall tag (R4, memory lifecycle design, Opus 2026-09-23) ──
            # Mark what this monologue recalled, so the writers can refuse to re-save it as new
            # evidence (helpers/memory_recall_tag.py). Placed before co-retrieval logging: that
            # call is not individually guarded, and a failure there must not skip the tag.
            if all_injected_ids:
                try:
                    import memory_recall_tag as mrt

                    n = mrt.tag(self.agent, all_injected_ids)
                    print(f"[MEM-ENHANCE] Recall tag: {len(all_injected_ids)} this pass, "
                          f"{n} this monologue", flush=True)
                except Exception as tag_err:
                    print(f"[MEM-ENHANCE] Recall tag skipped — {type(tag_err).__name__}", flush=True)

            # ── Recall trace (2026-09-24) ─────────────────────────────────
            # Every full run writes its row, `ids: []` included: "the hook ran and recalled
            # nothing" is a finding too. Before co-retrieval logging, for the tag's reason above.
            # `legacy` only when the helper rendered source clauses; without it there was no label.
            _trace(self.agent, all_injected_ids, turn, source=query_source,
                   error=pipeline_errors or None, dropped=dropped_ids,
                   legacy=legacy_ids if _trust is not None else None)
            traced = True

            # ── Co-retrieval logging ──────────────────────────────────────
            if all_injected_ids:
                _log_co_retrieval(
                    all_injected_ids, bst_domain, maint_cycle,
                )
                print("[MEM-ENHANCE] Co-retrieval logged", flush=True)

        except Exception as e:
            if not traced:
                _trace(self.agent, [], turn, early="exception", error=type(e).__name__)
            try:
                self.agent.context.log.log(
                    type="warning",
                    content=f"[MEM-ENHANCE] Error (passthrough): {e}",
                )
            except Exception:
                pass


# ── Recall trace ─────────────────────────────────────────────────────────────

def _trace(agent, ids, turn, source=None, early=None, error=None, dropped=None,
           legacy=None) -> None:
    """One row in the persistent recall trace (helpers/memory_recall_tag.trace). Never raises.

    `early` names a return before recall (subordinate / no_db / no_docs / no_query / exception):
    on such a turn A0's own untagged recall (_50/_91) stands, which is the A17 gap. `error` names
    the pipelines that raised ("memories", "solutions"), whose slots also keep A0's text.
    `dropped` lists the candidates the trust verdict withheld, and `legacy` the injected ids whose
    head showed "source: legacy" (graduated trust, Phase 1).

    The optional fields are passed only if the LOADED trace() accepts them (_accepts). A cached
    memory_recall_tag from an earlier deploy (2a: neither field; Phase 1: `dropped` only) then
    writes the row without them rather than losing it. A single retry on TypeError covered one
    field; it would lose the row on the second.

    !! memory_recall_tag is imported by bare name, so it sits in sys.modules and survives the
    plugins reload (modules.purge_namespace deletes only `plugins.*`; see recall_query.py's
    docstring). A deploy that adds trace() goes live at the next CONTAINER RESTART. Until then
    this prints that the trace is unavailable, and recall itself is unaffected.
    """
    try:
        import memory_recall_tag as mrt

        fn = getattr(mrt, "trace", None)
        if fn is None:
            print("[MEM-ENHANCE] Recall trace unavailable — the loaded memory_recall_tag predates "
                  "trace(); it loads at the next container restart", flush=True)
            return
        kwargs = {"turn": turn, "source": source, "early": early, "error": error}
        for name, value in (("dropped", dropped), ("legacy", legacy)):
            if value is not None and _accepts(fn, name):
                kwargs[name] = value
        fn(agent, ids, "_92", **kwargs)
    except Exception as trace_err:
        print(f"[MEM-ENHANCE] Recall trace skipped — {type(trace_err).__name__}", flush=True)


def _accepts(fn, name) -> bool:
    """Whether `fn` takes keyword `name` (or **kwargs). Unreadable signature: assume it does."""
    try:
        params = inspect.signature(fn).parameters
    except (TypeError, ValueError):
        return True
    return name in params or any(p.kind == p.VAR_KEYWORD for p in params.values())


def _legacy_ids(result) -> list:
    """Ids of the injected memories whose head showed "source: legacy" (GT-2a), the same
    source_clause that _with_provenance rendered. Empty when the helper is not loaded."""
    out = []
    if _trust is None:
        return out
    legacy = "source: " + getattr(_trust, "LEGACY_SOURCE", "legacy")
    for doc, _score in result:
        meta = getattr(doc, "metadata", None)
        did = meta.get("id") if isinstance(meta, dict) else None
        if not did:
            continue
        try:
            if _trust.source_clause(doc) == legacy:
                out.append(did)
        except Exception:
            pass
    return out


# ── Full Pipeline ────────────────────────────────────────────────────────────

async def _run_pipeline(
    db, all_docs, query, bst_domain, role_domains,
    sim_threshold, max_injected, area_filter,
    qe_config, decay_config, related_config,
    dropped=None,
) -> list[tuple]:
    """Run the 4-stage scoring pipeline: expand -> decay -> boost -> select.

    Returns [(doc, final_score)] for injection. `dropped`, when given, receives the ids of the
    candidates the trust verdict withheld (stage 2), for the recall trace.
    """
    # Stage 1: Query Expansion
    merged = await _query_expansion_search(
        db, query, bst_domain, sim_threshold, qe_config, area_filter,
    )
    print(f"[MEM-ENHANCE] Query expansion: {len(merged)} candidates from 3 queries", flush=True)
    if not merged:
        return []

    # Stage 2: Filter + Temporal Decay
    scored = _filter_and_decay(
        merged, all_docs, role_domains, decay_config, dropped=dropped,
    )
    print(f"[MEM-ENHANCE] After decay: {len(scored)} candidates", flush=True)
    if not scored:
        return []

    # Stage 3: Related Memory Boost
    scored = _apply_related_boost(
        scored, all_docs, max_injected, related_config,
    )

    # Stage 4: Top-K Selection
    return [(doc, score) for doc, score, _ in scored[:max_injected]]


# ── Stage 1: Query Expansion ─────────────────────────────────────────────────

async def _query_expansion_search(
    db, query, bst_domain, threshold, qe_config, area_filter,
) -> list[tuple]:
    """Run multi-variant FAISS queries and merge by memory ID.

    Returns [(doc, max_similarity_score)] with duplicates merged.
    """
    if not qe_config.get("enabled", True):
        # Single query fallback
        results = await db.search_similarity_threshold(
            query=query, limit=50, threshold=threshold,
            filter=area_filter,
        )
        return _unpack_results(results)

    k = qe_config.get("retrieval_k_per_variant", 8)
    max_kw = qe_config.get("max_keywords", 12)

    # Generate query variants
    queries = [query]  # 1. original

    if qe_config.get("use_keyword_extraction", True):
        kw_query = extract_keywords(query, max_kw)
        if kw_query and kw_query.strip() != query.lower().strip():
            queries.append(kw_query)  # 2. keyword-only

    if qe_config.get("use_domain_scoping", True) and bst_domain:
        kw_for_domain = extract_keywords(query, max_kw) or query
        domain_query = f"{bst_domain}: {kw_for_domain}"
        queries.append(domain_query)  # 3. domain-scoped

    # Run searches and merge by memory ID, keeping highest score
    merged = {}  # doc_id -> (doc, max_score)
    for q in queries:
        try:
            results = await db.search_similarity_threshold(
                query=q, limit=k, threshold=threshold,
                filter=area_filter,
            )
        except Exception:
            continue

        for item in results:
            doc, score = item if isinstance(item, tuple) else (item, 1.0)
            if not hasattr(doc, "metadata"):
                continue
            doc_id = doc.metadata.get("id", "")
            if not doc_id:
                continue
            if doc_id not in merged or score > merged[doc_id][1]:
                merged[doc_id] = (doc, score)

    return list(merged.values())


def _unpack_results(results) -> list[tuple]:
    """Unpack search results into [(doc, score)]."""
    unpacked = []
    for item in results:
        doc, score = item if isinstance(item, tuple) else (item, 1.0)
        if hasattr(doc, "metadata"):
            unpacked.append((doc, score))
    return unpacked


def extract_keywords(text: str, max_keywords: int = 12) -> str:
    """Deterministic keyword extraction: remove stopwords, cap at N terms."""
    words = re.findall(r"\b\w+\b", text.lower())
    keywords = [w for w in words if w not in STOPWORDS and len(w) > 2]
    return " ".join(keywords[:max_keywords])


# ── Stage 2: Filter + Temporal Decay ─────────────────────────────────────────

def _is_excluded(doc, cls) -> bool:
    """The trust verdict (helpers/memory_trust.excluded). When the helper is not loaded, the
    rule this filter applied inline before 2026-09-25, so recall never depends on the helper.
    (It is a bare-name import: absent when this file loaded means None until this file reloads,
    and once loaded, edits to it are live only after a container restart.)"""
    if _trust is not None:
        try:
            return bool(_trust.excluded(doc))
        except Exception:
            pass
    return cls.get("validity") == "deprecated"


def _filter_and_decay(
    merged_pool: list[tuple],
    all_docs: dict,
    role_domains: list,
    decay_config: dict,
    dropped=None,
) -> list[tuple]:
    """Apply validity/role filters and temporal decay scoring.

    Returns [(doc, blended_score, utility_rank)] sorted descending. `dropped`, when given,
    receives the id of each candidate the trust verdict withholds.
    """
    decay_enabled = decay_config.get("enabled", True)
    decay_weight = decay_config.get("decay_weight", 0.15)
    scored = []

    for doc, sim_score in merged_pool:
        cls = doc.metadata.get(CLS_KEY, {})
        lin = doc.metadata.get(LIN_KEY, {})

        # Trust verdict: exclude what may not be presented (helpers/memory_trust.py). The same
        # rule this filter always applied inline, `validity == "deprecated"`, now decided in one
        # place; runs BEFORE top-k, so a withheld memory's slot goes to the next candidate.
        if _is_excluded(doc, cls):
            if dropped is not None and doc.metadata.get("id"):
                dropped.append(doc.metadata["id"])
            continue

        # Role-relevance filter
        utility = cls.get("utility", "tactical")
        if role_domains and utility != "load_bearing":
            mem_domain = lin.get("bst_domain", "")
            if mem_domain and mem_domain not in role_domains:
                continue
            if not mem_domain:
                created_by = lin.get("created_by_role")
                if created_by and not _role_domain_overlaps(
                    created_by, role_domains
                ):
                    continue

        # Temporal decay
        if decay_enabled:
            recency = _calc_recency_score(doc.metadata, decay_config)
            blended = (
                (1 - decay_weight) * sim_score + decay_weight * recency
            )
        else:
            blended = sim_score

        utility_rank = _UTILITY_ORDER.get(utility, 0)
        scored.append((doc, blended, utility_rank))

    scored.sort(key=lambda x: (x[2], x[1]), reverse=True)
    return scored


def _calc_recency_score(doc_metadata: dict, decay_config: dict) -> float:
    """Exponential recency score. Returns 1.0 for exempt memories."""
    cls = doc_metadata.get(CLS_KEY, {})
    lin = doc_metadata.get(LIN_KEY, {})

    # Exemption checks
    if cls.get("utility") in decay_config.get("exempt_utilities", []):
        return 1.0
    if cls.get("source") in decay_config.get("exempt_sources", []):
        return 1.0
    if cls.get("validity") in decay_config.get("exempt_validities", []):
        return 1.0
    relational_salience = cls.get("relational_salience", "task_transient")
    if relational_salience in decay_config.get("exempt_relational_salience", []):
        return 1.0  # relationship_defining memories never decay

    # Age calculation: prefer last_accessed, fallback created_at, timestamp
    time_ref = (
        lin.get("last_accessed")
        or lin.get("created_at")
        or doc_metadata.get("timestamp")
    )
    if not time_ref:
        return 1.0

    try:
        ref_dt = datetime.fromisoformat(time_ref)
        if ref_dt.tzinfo is None:
            ref_dt = ref_dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        age_hours = max(0, (now - ref_dt).total_seconds() / 3600)
    except Exception:
        return 1.0

    half_life = decay_config.get("half_life_hours", 168)
    if half_life <= 0:
        return 1.0

    # collaboration_history gets extended half-life (slower decay)
    if relational_salience == "collaboration_history":
        multiplier = decay_config.get("collaboration_history_half_life_multiplier", 2.0)
        half_life = half_life * multiplier

    decay_rate = math.log(2) / half_life
    recency = math.exp(-decay_rate * age_hours)

    min_score = decay_config.get("min_recency_score", 0.1)
    return max(min_score, recency)


# ── Stage 3: Related Memory Boost ────────────────────────────────────────────

def _apply_related_boost(
    scored: list[tuple],
    all_docs: dict,
    max_injected: int,
    related_config: dict,
) -> list[tuple]:
    """Boost near-cutoff memories that are linked to top-k selections.

    Returns re-sorted scored list.
    """
    if not related_config.get("enabled", True):
        return scored

    if len(scored) <= max_injected:
        return scored  # Everything fits, no boosting needed

    boost = related_config.get("related_boost", 0.08)

    # Collect related IDs from preliminary top-k
    related_ids = set()
    for doc, _, _ in scored[:max_injected]:
        if not hasattr(doc, "metadata"):
            continue
        lin = doc.metadata.get(LIN_KEY, {})
        rids = lin.get("related_memory_ids", [])
        if isinstance(rids, list):
            related_ids.update(rids)

    if not related_ids:
        return scored

    # Boost related memories that are below the cutoff
    boosted = False
    for i in range(max_injected, len(scored)):
        doc, score, util_rank = scored[i]
        if not hasattr(doc, "metadata"):
            continue
        doc_id = doc.metadata.get("id", "")
        if doc_id in related_ids:
            scored[i] = (doc, score + boost, util_rank)
            boosted = True

    if boosted:
        scored.sort(key=lambda x: (x[2], x[1]), reverse=True)

    return scored


# ── BST Domain Access ────────────────────────────────────────────────────────

def _get_bst_domain(agent) -> str:
    """Get current BST domain classification from agent context."""
    try:
        store = getattr(agent, BST_STORE_KEY, {})
        belief = store.get(BST_BELIEF_KEY)
        return belief.get("domain", "") if belief else ""
    except Exception:
        return ""


# ── Query Extraction ─────────────────────────────────────────────────────────

def _get_query(agent, loop_data, config=None) -> str:
    """The text handed to the embedder. Delegates to the shared rule.

    Was: `loop_data.user_message.output_text()`, unbounded. Measured 2026-09-16 — that overflowed
    nomic-embed-v1.5's 2,048-token ceiling on 919 of 2,882 embedding requests, EVERY truncated one
    a recall query, and on an idle cycle it was the same activation charge every turn (785 of them
    at exactly 2,120 tokens), which returned the same six memories all day.

    The rule now lives in `helpers/recall_query.py` so `_55` and this file cannot drift apart —
    they carried byte-identical copies of the old function, which is how drift starts.

    Falls back to the previous behaviour if the helper is unavailable: a missing helper must not
    cost recall entirely, and the old behaviour is bad rather than dangerous.
    """
    return _get_query_with_source(agent, loop_data, config)[0]


def _get_query_with_source(agent, loop_data, config=None):
    """(query, source): `_get_query`'s text, and which rule produced it, for the recall trace.

    source is recall_query's class (recent_work / idle_charge / user_message), or:
      "unrecorded"   the loaded helper predates build_query_with_source. recall_query is imported
                     by bare name and survives plugin reloads until a container restart, so this
                     is the state between a deploy and the restart. The query still comes from
                     build_query, so it is still bounded; only the label is missing.
      "fallback_raw" the helper is unavailable; the raw user message, unbounded (as before).
    """
    max_chars = None
    if isinstance(config, dict):
        max_chars = (config.get("recall_query") or {}).get("max_chars")
    try:
        if recall_query is None:
            raise ImportError("recall_query helper not on sys.path")
        limit = max_chars or recall_query.DEFAULT_MAX_CHARS
        with_source = getattr(recall_query, "build_query_with_source", None)
        if with_source is None:
            return recall_query.build_query(agent, loop_data, limit), "unrecorded"
        return with_source(agent, loop_data, limit)
    except Exception as e:
        print(f"[MEM-ENHANCE] recall_query helper unavailable ({type(e).__name__}) — "
              "falling back to the raw user message", flush=True)
        if hasattr(loop_data, "user_message") and loop_data.user_message:
            try:
                if hasattr(loop_data.user_message, "output_text"):
                    return loop_data.user_message.output_text(), "fallback_raw"
                return str(loop_data.user_message), "fallback_raw"
            except Exception:
                pass
        return "", "fallback_raw"


# ── Role Domain Check ────────────────────────────────────────────────────────

def _role_domain_overlaps(
    created_by_role: str, current_domains: list,
) -> bool:
    """Check if the creating role's domains overlap with current role."""
    try:
        path = os.path.join(ROLES_DIR, f"{created_by_role}.json")
        if not os.path.isfile(path):
            return True
        with open(path, "r", encoding="utf-8") as f:
            profile = json.load(f)
        creator_domains = profile.get(
            "capabilities", {}
        ).get("bst_domains", [])
        return bool(set(creator_domains) & set(current_domains))
    except Exception:
        return True


# ── Access Tracking ──────────────────────────────────────────────────────────

# An observed_at the head may show: an ISO date at its start. Anything else falls back to "saved".
_ISO_DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _with_provenance(result, observations=None, config=None, now=None):
    """Prefix each recalled memory with what it is and when it was saved.

    WHY, measured 2026-09-19. A memory arrives in the [EXTRAS] block as BARE PROSE — no
    provenance, no date — so a quotation inside a memory is typographically indistinguishable
    from an instruction issued this turn.

    Aporia reported that injected directives were arriving through the EXTRAS field, citing
    `User explicitly requested: Reply with just OK`. Traced: that string exists in exactly two
    places in her store, BOTH her own notes about the phenomenon, and in the chat she describes
    the EXTRAS block contains her 2026-09-17 warning verbatim with the directive appearing ONCE,
    inside its own quotation. Nothing was injected. Her record of the thing reproduced the
    appearance of the thing — and each time she flags it she writes another memory containing
    the quote, so it compounds. Same shape as the filtering-rule accretion, benign in content
    and self-sustaining in form.

    Dating the recollection makes a quoted imperative unmistakably historical. Her refusal of
    unattributed directives is correct and unaffected: this removes the ambiguity rather than
    asking her to resolve it on every turn.

    RENDER-TIME ONLY. `page_content` is what was saved and stays what was saved. A prefix that
    reached the store would be re-recalled and re-prefixed next turn, which is the compounding
    shape one layer down.

    R3 (memory lifecycle design, 2026-09-23) adds clauses to the same head, also at render time
    only (helpers/memory_temporal.py): a state observation past its stale threshold says how
    old it is, and an unkeyed memory that names a keyed subject says when a newer observation of
    that subject exists. The save date stays first; a memory with neither clause renders
    exactly as before.

    Graduated trust (Phase 1, 2026-09-25) adds one clause after the date, from
    helpers/memory_trust.render_trust: "source: <stored value>" when the memory carries the
    derivation marker (classification.source_rule), else "source: legacy" (GT-2a). If the helper
    cannot load, the head is exactly as before.
    """
    now = now or datetime.now(timezone.utc)
    out = []
    for doc, _score in result:
        text = getattr(doc, "page_content", "") or ""
        meta = getattr(doc, "metadata", None) or {}
        stamp = str(meta.get("timestamp") or "")[:10]   # YYYY-MM-DD
        # The date's WORD follows its field (Opus's ruling, 2026-09-25): A0 core consolidation
        # (_memory/helpers/memory_consolidation._handle_merge) rewrites `timestamp` to the merge
        # time, so a merged memory read "saved <today>" for older content. R3's observed_at survives
        # a merge; when present the head says "observed <date>", never "saved" with an
        # observation date.
        observed = str(meta.get("observed_at") or "")[:10]
        # An undated memory says so. Silently omitting the date would make it read as
        # current, which is the defect; guessing one would be worse.
        if _ISO_DAY.match(observed):
            clauses = ["observed %s" % observed]
        else:
            clauses = [("saved %s" % stamp) if stamp else "save date unknown"]
        # Graduated trust GT-2a (helpers/memory_trust.py): the source, shown only when a
        # derivation rule produced it, else "legacy". Same head, no second frame.
        if _trust is not None:
            try:
                clauses += _trust.render_trust(doc)[1]
            except Exception:
                pass
        if _mt is not None:
            try:
                clauses += _mt.frame_clauses(doc, observations or {}, now, config)
            except Exception:
                pass
        head = "recalled memory (%s):" % "; ".join(clauses)
        out.append(head + "\n" + text)
    return "\n\n".join(out)


def _update_access(
    filtered_results: list[tuple], all_docs: dict,
) -> list[str]:
    """Increment access_count on injected memories. Returns list of IDs."""
    now = datetime.now(timezone.utc).isoformat()
    injected_ids = []

    for doc, _ in filtered_results:
        if not hasattr(doc, "metadata"):
            continue
        doc_id = doc.metadata.get("id", "")
        if not doc_id:
            continue

        injected_ids.append(doc_id)

        # Update ORIGINAL document in docstore (not the search copy)
        original = all_docs.get(doc_id)
        if not original or not hasattr(original, "metadata"):
            continue

        lin = original.metadata.get(LIN_KEY)
        if not lin:
            lin = {
                "created_at": original.metadata.get("timestamp", now),
                "created_by_role": None,
                "bst_domain": "",
                "classified_at_cycle": 0,
                "supersedes": None,
                "superseded_by": None,
                "access_count": 0,
                "last_accessed": None,
                "related_memory_ids": [],
            }
            original.metadata[LIN_KEY] = lin

        lin["access_count"] = lin.get("access_count", 0) + 1
        lin["last_accessed"] = now

    return injected_ids


# ── Co-Retrieval Logging ─────────────────────────────────────────────────────

def _log_co_retrieval(
    memory_ids: list[str], query_domain: str, cycle: int,
):
    """Append co-retrieval entry. FIFO eviction at max_entries."""
    if len(memory_ids) < 2:
        return

    log_data = {"max_entries": MAX_CO_RETRIEVAL_ENTRIES, "entries": []}
    try:
        if os.path.isfile(CO_RETRIEVAL_LOG):
            with open(CO_RETRIEVAL_LOG, "r", encoding="utf-8") as f:
                log_data = json.load(f)
    except Exception:
        pass

    entries = log_data.get("entries", [])
    max_entries = log_data.get("max_entries", MAX_CO_RETRIEVAL_ENTRIES)

    entries.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "query_domain": query_domain,
        "memory_ids": memory_ids,
        "cycle": cycle,
    })

    if len(entries) > max_entries:
        entries = entries[-max_entries:]

    log_data["entries"] = entries
    if "cluster_candidates" not in log_data:
        log_data["cluster_candidates"] = []

    try:
        os.makedirs(os.path.dirname(CO_RETRIEVAL_LOG), exist_ok=True)
        with open(CO_RETRIEVAL_LOG, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2)
    except Exception:
        pass


# ── Model Profile Loading ────────────────────────────────────────────────────

def _resolve_model_id() -> str:
    """Active chat-model id: settings.json → _model_config plugin (v2/v17), @-suffix stripped."""
    name = ""
    try:
        with open("/a0/usr/settings.json", encoding="utf-8") as f:
            name = json.load(f).get("chat_model_name", "") or ""
    except Exception:
        pass
    if not name:
        try:
            with open(MODEL_CONFIG_PATH, encoding="utf-8") as f:
                name = str(json.load(f).get("chat_model", {}).get("name", "") or "")
        except Exception:
            pass
    return name.split("@")[0].strip()


def _load_profile_memory_section() -> dict:
    """Load the memory section from the ACTIVE model's profile (not an arbitrary one)."""
    try:
        if not os.path.isdir(PROFILE_DIR):
            return {}
        model_id = _resolve_model_id()
        profile_path = os.path.join(PROFILE_DIR, f"{model_id}.json") if model_id else ""
        if not profile_path or not os.path.isfile(profile_path):
            profile_path = os.path.join(PROFILE_DIR, "default.json")
        if not os.path.isfile(profile_path):
            return {}
        with open(profile_path, "r", encoding="utf-8") as f:
            return json.load(f).get("memory", {})
    except Exception:
        return {}


# ── Config Loading ───────────────────────────────────────────────────────────

def _load_config() -> dict:
    """Load classification config with defaults."""
    try:
        if os.path.isfile(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                user_config = json.load(f)
            merged = dict(DEFAULT_CONFIG)
            merged.update(user_config)
            return merged
    except Exception:
        pass
    return dict(DEFAULT_CONFIG)
