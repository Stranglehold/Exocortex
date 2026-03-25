"""
Evidence Ledger Recorder — Epistemic Integrity Layer
=====================================================
Hook: tool_execute_after (_25_)

Records every tool output to the session evidence ledger on agent data.
Runs after Error Comprehension (_20_) and before Fallback Logger (_30_).

The ledger is consumed by _25_epistemic_integrity.py (monologue_end) to
ground-check factual claims in model output against data that actually
entered this session.

Ledger structure (stored at agent._evidence_ledger):
  {
    "session_start": ISO timestamp,
    "entries": [{ tool, ts, summary, kv }],
    "key_values": [normalized value strings for fast lookup]
  }

No LLM calls. Pure record-keeping.
"""

import re
import uuid
from datetime import datetime, timezone
from typing import Any

from python.helpers.extension import Extension
from python.helpers.tool import Response

LEDGER_KEY = "_evidence_ledger"

# Max chars to store per entry (enough for value extraction + summary)
MAX_CONTENT_CHARS = 1500

# Tools whose outputs are config/meta, not data — skip recording
SKIP_TOOLS = {"response"}


class EvidenceLedgerRecorder(Extension):
    """Records tool outputs to the session evidence ledger."""

    async def execute(self, response: Response | None = None, **kwargs) -> Any:
        try:
            tool_name = kwargs.get("tool_name", "")

            if tool_name in SKIP_TOOLS:
                return

            if not response or not response.message:
                return

            content = response.message[:MAX_CONTENT_CHARS]

            # Get or initialize ledger
            ledger = self.agent.get_data(LEDGER_KEY)
            if not ledger:
                ledger = {
                    "session_start": datetime.now(timezone.utc).isoformat(),
                    "entries": [],
                    "key_values": [],
                }

            key_values = list(_extract_key_values(content))

            # Assign staging ID for rollback cross-reference
            staging_id = str(uuid.uuid4())[:8]

            entry = {
                "tool": tool_name,
                "ts": datetime.now(timezone.utc).isoformat(),
                "summary": content[:300],
                "kv": key_values,
                "_staging_id": staging_id,
            }

            # Tag if written during an active loop
            if self.agent.get_data("_loop_active"):
                entry["loop_period"] = True

            ledger["entries"].append(entry)

            # Extend cumulative key_values set (stored as list for JSON serialization)
            existing = set(ledger.get("key_values", []))
            existing.update(key_values)
            ledger["key_values"] = list(existing)

            self.agent.set_data(LEDGER_KEY, ledger)

            # Staging buffer: record this write for potential surgery rollback
            try:
                if self.agent.get_data("_loop_active"):
                    staging = self.agent.get_data("_memory_staging_buffer") or []
                    staging.append({
                        "turn_idx": len(ledger["entries"]) - 1,
                        "store": "evidence_ledger",
                        "doc_id": staging_id,
                        "written_at": entry["ts"],
                    })
                    self.agent.set_data("_memory_staging_buffer", staging)
            except Exception:
                pass

        except Exception:
            pass


# ── Key Value Extraction ─────────────────────────────────────────────────────


def _extract_key_values(text: str) -> set:
    """Extract specific numeric/rating/temporal values from text for grounding lookup."""
    values = set()

    # Currency with scale: $30 billion, $1.5B, $800M
    for m in re.findall(r'\$[\d,.]+\s*(?:billion|million|trillion)\b', text, re.IGNORECASE):
        values.add(_normalize_scale(m))
    for m in re.findall(r'\$[\d,.]+\s*[BMTbmt]\b', text):
        values.add(m.strip().upper())

    # Large standalone dollar amounts: $30.5, $1,234
    for m in re.findall(r'\$\d[\d,.]{2,}', text):
        values.add(m.replace(',', ''))

    # Percentages: 25.4%, 0.88%
    for m in re.findall(r'\b\d+\.?\d*\s*%', text):
        values.add(m.replace(' ', ''))

    # Financial ratios: 1.5x, 2.8×
    for m in re.findall(r'\b\d+\.?\d+\s*[x×]\b', text, re.IGNORECASE):
        values.add(m.strip())

    # Credit ratings: AAA, AA+, Baa1, BBB-
    for m in re.findall(
        r'\b(?:AAA|AA[+-]?|A[+-]?|BBB[+-]?|BB[+-]?|B[+-]?|Baa[1-3]|Ba[1-3]|B[1-3])\b',
        text
    ):
        if len(m) >= 2:
            values.add(m)

    # Fiscal periods: Q3 2024, FY2025, 2024-Q4
    for m in re.findall(r'\b(?:Q[1-4]\s+)?(?:FY\s*)?20\d{2}\b', text):
        values.add(m.strip())

    return values


def _normalize_scale(s: str) -> str:
    """Normalize: '$1.5 billion' → '$1.5B'"""
    s = s.strip()
    for word, abbr in [('trillion', 'T'), ('billion', 'B'), ('million', 'M')]:
        if word.lower() in s.lower():
            num = re.search(r'[\d,.]+', s)
            if num:
                return f"${num.group().replace(',', '')}{abbr}"
    return s
