"""
silence.py — Detects what's NOT being said.

Compares factual element inventories across ideologically distinct source
clusters on the same topic. Elements present in some clusters but absent
from others are flagged as silence candidates.

LLM-based element extraction: one call per topic per run, combining claim
texts from each cluster. No embedding required — presence/absence is the
signal.
"""
import logging
import os
import re
from datetime import datetime, timezone

from .db import jloads, jdumps

log = logging.getLogger("[SILENCE]")

LLM_URL   = os.environ.get("OSS_LLM_URL",   "http://host.docker.internal:1236/v1")
from .llm_config import get_llm_model as _get_llm_model
LLM_MODEL = _get_llm_model()

_DISTINCT_CLUSTERS = {"left", "right", "center", "international", "independent"}


# ---------------------------------------------------------------------------
# LLM element extraction
# ---------------------------------------------------------------------------

def _get_llm():
    try:
        from openai import OpenAI  # noqa: PLC0415
        return OpenAI(base_url=LLM_URL, api_key="local")
    except Exception as e:
        log.warning(f"LLM client unavailable: {e}")
        return None


def _strip_thinking(raw: str) -> str:
    return re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()


def _extract_elements(claim_texts: list, llm) -> list:
    """
    Call LLM once with combined claim texts to get key factual elements.
    Returns a list of short element strings (names, events, numbers, claims).
    Falls back to simple noun-phrase extraction on LLM failure.
    """
    if not claim_texts:
        return []

    combined = " ".join(claim_texts[:20])[:4000]
    prompt = (
        "Extract the key factual elements from these news claims. "
        "An element is a specific named entity, event, statistic, actor, or location "
        "that could be reported or omitted. Return a JSON array of short strings "
        "(3-8 words each). No duplicates. No explanations.\n\n"
        f"Claims:\n{combined}\n\nReturn only the JSON array."
    )
    try:
        resp = llm.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=512,
        )
        raw = _strip_thinking(resp.choices[0].message.content)
        raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
        raw = re.sub(r"\s*```$", "", raw)
        import json  # noqa: PLC0415
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [str(e).strip() for e in parsed if e]
        return []
    except Exception as e:
        log.warning(f"_extract_elements LLM failed: {e} — falling back to n-gram heuristic")
        return _ngram_elements(combined)


def _ngram_elements(text: str) -> list:
    """Simple fallback: extract capitalized 2-3 word sequences as candidate elements."""
    pattern = re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b')
    matches = list(dict.fromkeys(pattern.findall(text)))  # dedup, preserve order
    return matches[:40]


# ---------------------------------------------------------------------------
# Silence scan
# ---------------------------------------------------------------------------

def run_silence_scan(conn, topic_tag: str) -> int:
    """
    For a given topic, compare element inventories across distinct source clusters.
    Flag elements present in ≥1 cluster but absent from ≥1 other cluster.
    Inserts into silence_flags table. Returns count of new flags.
    """
    inserted = 0
    try:
        cur = conn.cursor()
        # Fetch recent claims on this topic, grouped by cluster
        cur.execute("""
            SELECT c.claim_text, s.cluster
            FROM claims c
            JOIN sources s ON s.id = c.source_id
            WHERE EXISTS (SELECT 1 FROM json_each(c.topic_tags) WHERE value=?)
              AND c.trust_level IN ('STAGED','PROMOTED')
              AND c.extracted_at >= datetime('now', '-72 hours')
            ORDER BY s.cluster
        """, (topic_tag,))
        rows = cur.fetchall()

        if not rows:
            return 0

        # Bucket by cluster
        cluster_texts: dict = {}
        for row in rows:
            cluster = row["cluster"]
            if cluster in _DISTINCT_CLUSTERS:
                cluster_texts.setdefault(cluster, []).append(row["claim_text"])

        if len(cluster_texts) < 2:
            return 0

        # Extract elements per cluster
        llm = _get_llm()
        cluster_elements: dict = {}
        for cluster, texts in cluster_texts.items():
            if llm:
                elements = _extract_elements(texts, llm)
            else:
                combined = " ".join(texts[:10])[:2000]
                elements = _ngram_elements(combined)
            cluster_elements[cluster] = set(elements)

        # Find elements present in some clusters but absent from others
        all_clusters = list(cluster_elements.keys())
        now = datetime.now(timezone.utc).isoformat()

        for element in set().union(*cluster_elements.values()):
            present_in = [c for c in all_clusters if element in cluster_elements[c]]
            absent_from = [c for c in all_clusters if element not in cluster_elements[c]]

            if not present_in or not absent_from:
                continue

            # Skip if this silence flag already exists (same topic + element within 24h)
            cur.execute("""
                SELECT id FROM silence_flags
                WHERE topic_tag=? AND element=?
                  AND first_detected >= datetime('now', '-24 hours')
            """, (topic_tag, element))
            if cur.fetchone():
                continue

            # Map clusters → source names for context
            present_sources: list = []
            absent_sources: list = []
            for cluster in present_in:
                cur.execute(
                    "SELECT name FROM sources WHERE cluster=? LIMIT 3", (cluster,)
                )
                present_sources += [r["name"] for r in cur.fetchall()]
            for cluster in absent_from:
                cur.execute(
                    "SELECT name FROM sources WHERE cluster=? LIMIT 3", (cluster,)
                )
                absent_sources += [r["name"] for r in cur.fetchall()]

            try:
                conn.execute("""
                    INSERT INTO silence_flags
                        (topic_tag, element, present_in_sources, absent_from_sources,
                         present_in_clusters, absent_from_clusters,
                         first_detected, detection_method)
                    VALUES (?,?,?,?,?,?,?,'comparative')
                """, (
                    topic_tag,
                    element,
                    jdumps(present_sources),
                    jdumps(absent_sources),
                    jdumps(present_in),
                    jdumps(absent_from),
                    now,
                ))
                conn.commit()
                inserted += 1
            except Exception as e:
                log.warning(f"Insert silence_flag failed for '{element}': {e}")

    except Exception as e:
        log.warning(f"run_silence_scan failed for topic={topic_tag}: {e}")

    return inserted


# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------

def get_silence_flags(conn, topic_tag: str, since: str = None) -> list:
    """Return silence flags for a topic, newest first."""
    try:
        cur = conn.cursor()
        params: list = [topic_tag]
        since_clause = ""
        if since:
            since_clause = "AND first_detected >= ?"
            params.append(since)
        cur.execute(
            f"SELECT * FROM silence_flags WHERE topic_tag=? {since_clause} "
            f"ORDER BY id DESC",
            params,
        )
        return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        log.warning(f"get_silence_flags failed: {e}")
        return []
