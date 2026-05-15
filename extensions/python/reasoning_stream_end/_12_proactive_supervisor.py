"""
Proactive Reasoning Supervisor — Analysis Hook
===============================================
Hook: reasoning_stream_end
Priority: _12 (v1.6 path: extensions/python/reasoning_stream_end/)

Fires once after the model's full reasoning block is generated,
BEFORE process_tools() parses and dispatches the tool call.

Reads the reasoning buffer accumulated by the companion
reasoning_stream hook, runs five deterministic signal detectors,
and sets typed flags for the before_main_llm_call hook to read
on the NEXT turn and inject targeted corrections.

Signal Classes (Phase 1 — pattern matching baseline):
  1. repeated_sentence    — same analytical sentence appears 2+ times
  2. repeated_tool        — same tool considered 3+ times with action verbs
  3. self_reference_loop  — model references prior failed attempts 2+ times
  4. hedge_without_commit — hedge:commit ratio > 3:1 in reasoning
  5. excessive_deliberation — reasoning length exceeds task-class threshold

All detection is deterministic: regex, string similarity (difflib),
statistical thresholds. No LLM calls. Faster than generation.

Coordination: sets _ps_fired flag read by _50_supervisor_loop at
message_loop_end — Tier 1 loop injection defers when this flag is True.

Also writes behavioral trace JSONL for Phase 2 calibration data collection.

Log tag: [PS-ANALYZE]
"""

import difflib
import json
import os
import re
import time
from dataclasses import asdict, dataclass
from typing import Optional

from agent import LoopData
from helpers.extension import Extension

# ── Agent data keys (shared with buffer and injection hooks) ──────────────────

RS_BUF_KEY    = "_ps_rs_buf"    # set by reasoning_stream hook
PS_SIGNAL_KEY = "_ps_signal"    # dict: signal analysis result for next turn
PS_FIRED_KEY  = "_ps_fired"     # bool: intervention queued for next turn

# BST domain key (set by _11_belief_state_tracker)
BST_STORE_KEY = "_bst_store"

# Behavioral trace log path (Phase 2 training data)
TRACE_LOG_PATH = "/a0/usr/Exocortex/behavioral_traces.jsonl"

# ── Configuration (Phase 1 static thresholds) ─────────────────────────────────

# Signal 1: minimum similarity ratio to flag two sentences as repeated
REPEATED_SENTENCE_SIMILARITY = 0.80
# Signal 1: minimum sentence length to include in similarity comparison
REPEATED_SENTENCE_MIN_CHARS  = 20
# Signal 1: severity per repetition above the first occurrence
REPEATED_SENTENCE_SEVERITY_PER = 0.4

# Signal 2: how many times the same tool must appear with action verbs to flag
REPEATED_TOOL_COUNT = 3
# Signal 2: severity per mention above (REPEATED_TOOL_COUNT - 1)
REPEATED_TOOL_SEVERITY_PER = 0.3
# Signal 2: extra severity for call_subordinate (depth risk)
REPEATED_SUBORDINATE_EXTRA = 0.2

# Signal 3: how many self-reference phrases before flagging
SELF_REF_COUNT = 2
SELF_REF_SEVERITY = 0.5

# Signal 4: hedge:commit ratio threshold
HEDGE_COMMIT_RATIO = 3.0
HEDGE_COMMIT_SEVERITY = 0.3

# Signal 5: reasoning length thresholds per task class (chars)
DELIBERATION_THRESHOLDS = {
    "utility":    1500,
    "analytical": 3000,
    "code":       2500,
    "creative":   2000,
    "default":    2000,
}

# BST domain → deliberation class mapping
DOMAIN_CLASS_MAP = {
    # Utility class — simple tasks, short reasoning expected
    "conversation":     "utility",
    "greeting":         "utility",
    "clarification":    "utility",
    "simple_qa":        "utility",
    "meta_cognitive":   "utility",
    # Analytical class — research, investigation, complex reasoning
    "planning":         "analytical",
    "analysis":         "analytical",
    "research":         "analytical",
    "investigation":    "analytical",
    "agentic":          "analytical",
    # Code class — implementation, debugging, system admin
    "codegen":          "code",
    "debugging":        "code",
    "system_admin":     "code",
    "file_ops":         "code",
    # Creative class
    "creative":         "creative",
}

# Minimum severity required to set the _ps_fired flag
SEVERITY_THRESHOLD_FOR_INTERVENTION = 0.4

# ── Signal dataclass ──────────────────────────────────────────────────────────

@dataclass
class ReasoningSignal:
    signal_class: str    # one of the 5 class names
    severity: float      # 0.0–1.0
    evidence: str        # brief description for logging only (never injected)
    tool_name: str = ""  # relevant tool for repeated_tool signal


# ── Signal detection regexes ──────────────────────────────────────────────────

# Signal 2: action verbs + tool-like names
_TOOL_ACTION_RX = re.compile(
    r"(?:call|use|run|try|execute|invoke|utilize)\s+"
    r"([\w]+(?:_tool|_agent|_subordinate|_search|_query|_engine)?)",
    re.IGNORECASE,
)

# Signal 3: self-reference phrases
_SELF_REF_RX = re.compile(
    r"(?:i already tried|as i mentioned|i said earlier|i've already|i have already"
    r"|i previously|i attempted|i already did|i did that already|i tried that)",
    re.IGNORECASE,
)

# Signal 4: hedge phrases
_HEDGE_RX = re.compile(
    r"(?:maybe i should|i could try|perhaps|i might|possibly|i'm not sure"
    r"|i am not sure|not sure (if|whether|how)|i'm uncertain|i wonder if"
    r"|it's unclear|it is unclear|i don't know if|i do not know if)",
    re.IGNORECASE,
)

# Signal 4: commitment phrases
_COMMIT_RX = re.compile(
    r"(?:i will |i'll |the answer is|my solution is|i'm going to |i am going to "
    r"|the solution is|i should use|let me use|i need to use|i'll call|i will call)",
    re.IGNORECASE,
)

# ── Tool alternatives (for intervention text) ─────────────────────────────────

# Lightweight suggestion map — what to try when a specific tool keeps failing
_TOOL_ALTERNATIVES = {
    "code_execution_tool": "response (report what you know), search_engine (verify facts first)",
    "search_engine":       "code_execution_tool (compute directly), response (answer from knowledge)",
    "memory_load":         "response (use current context), code_execution_tool (read file directly)",
    "memory_save":         "response (confirm and continue)",
    "call_subordinate":    "code_execution_tool (do it directly), response (report current findings)",
    "browser_agent":       "search_engine, code_execution_tool (curl/requests)",
    "document_query":      "code_execution_tool (read file), memory_load",
}


# ── Extension ─────────────────────────────────────────────────────────────────

class ProactiveSupervisorAnalyzer(Extension):
    """reasoning_stream_end: analyze buffered reasoning, set intervention flags."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> None:
        try:
            # Read the reasoning buffer set by the companion buffer hook
            text = self.agent.get_data(RS_BUF_KEY) or ""

            # Clear buffer immediately — prevents stale analysis on turns without reasoning
            self.agent.set_data(RS_BUF_KEY, "")

            if not text or len(text) < 50:
                # No substantive reasoning — clear any stale signal, nothing to analyze
                self.agent.set_data(PS_SIGNAL_KEY, None)
                self.agent.set_data(PS_FIRED_KEY, False)
                return

            # Get BST domain for task-class-aware thresholds
            # BST stores belief state at _bst_store["__bst_belief_state__"]["domain"]
            bst_store = getattr(self.agent, BST_STORE_KEY, {}) or {}
            bst_domain = bst_store.get("__bst_belief_state__", {}).get("domain", "") or ""
            task_class = DOMAIN_CLASS_MAP.get(bst_domain, "default")

            # Run all five detectors, collect signals
            signals = []
            _detect_repeated_sentence(text, signals)
            _detect_repeated_tool(text, signals)
            _detect_self_reference(text, signals)
            _detect_hedge_without_commit(text, signals)
            _detect_excessive_deliberation(text, task_class, signals)

            # Select the highest-severity signal
            best = max(signals, key=lambda s: s.severity) if signals else None

            # Write behavioral trace regardless of whether we intervene
            _write_behavioral_trace(
                agent=self.agent,
                text=text,
                task_class=task_class,
                bst_domain=bst_domain,
                signals=signals,
            )

            if best and best.severity >= SEVERITY_THRESHOLD_FOR_INTERVENTION:
                signal_dict = {
                    "signal_class": best.signal_class,
                    "severity": best.severity,
                    "evidence": best.evidence,
                    "tool_name": best.tool_name,
                }
                self.agent.set_data(PS_SIGNAL_KEY, signal_dict)
                self.agent.set_data(PS_FIRED_KEY, True)
                print(
                    f"[PS-ANALYZE] SIGNAL {best.signal_class} "
                    f"severity={best.severity:.2f} domain={bst_domain or 'none'} "
                    f"len={len(text)} | {best.evidence}",
                    flush=True,
                )
            else:
                self.agent.set_data(PS_SIGNAL_KEY, None)
                self.agent.set_data(PS_FIRED_KEY, False)
                if signals:
                    print(
                        f"[PS-ANALYZE] signals below threshold "
                        f"(best={best.signal_class if best else 'none'} "
                        f"sev={best.severity:.2f if best else 0:.2f}) domain={bst_domain or 'none'} "
                        f"len={len(text)}",
                        flush=True,
                    )

        except Exception as e:
            # Always clear flags on error — don't leave stale True flags
            try:
                self.agent.set_data(PS_FIRED_KEY, False)
                self.agent.set_data(PS_SIGNAL_KEY, None)
            except Exception:
                pass
            print(f"[PS-ANALYZE] Error (passthrough): {e}", flush=True)


# ── Signal Detectors ──────────────────────────────────────────────────────────

def _sentences(text: str) -> list:
    """Split text into sentences, filtering by minimum length."""
    # Split on sentence-ending punctuation followed by whitespace or end-of-string
    raw = re.split(r"(?<=[.!?])\s+|\n{2,}", text)
    return [s.strip() for s in raw if len(s.strip()) >= REPEATED_SENTENCE_MIN_CHARS]


def _detect_repeated_sentence(text: str, out: list) -> None:
    """
    Signal 1: same analytical sentence appears 2+ times.
    Uses pairwise difflib similarity across all sentences > MIN_CHARS.
    """
    sentences = _sentences(text)
    if len(sentences) < 2:
        return

    repetitions = 0
    seen_pairs = set()

    for i in range(len(sentences)):
        for j in range(i + 1, len(sentences)):
            key = (min(i, j), max(i, j))
            if key in seen_pairs:
                continue
            seen_pairs.add(key)
            ratio = difflib.SequenceMatcher(
                None, sentences[i].lower(), sentences[j].lower()
            ).ratio()
            if ratio >= REPEATED_SENTENCE_SIMILARITY:
                repetitions += 1

    if repetitions >= 1:
        severity = min(1.0, repetitions * REPEATED_SENTENCE_SEVERITY_PER)
        out.append(ReasoningSignal(
            signal_class="repeated_sentence",
            severity=severity,
            evidence=f"{repetitions} similar sentence pair(s) found (threshold {REPEATED_SENTENCE_SIMILARITY:.0%})",
        ))


def _detect_repeated_tool(text: str, out: list) -> None:
    """
    Signal 2: same tool name mentioned 3+ times with action verbs.
    Extra severity for call_subordinate (subordinate depth risk).
    """
    matches = _TOOL_ACTION_RX.findall(text.lower())
    if not matches:
        return

    # Count per tool name
    counts: dict = {}
    for m in matches:
        tool = m.strip("_")  # normalize slightly
        counts[tool] = counts.get(tool, 0) + 1

    worst_tool = max(counts, key=counts.get)
    worst_count = counts[worst_tool]

    if worst_count >= REPEATED_TOOL_COUNT:
        excess = worst_count - (REPEATED_TOOL_COUNT - 1)
        severity = min(1.0, excess * REPEATED_TOOL_SEVERITY_PER)
        # Extra severity for subordinate depth risk
        if "subordinate" in worst_tool:
            severity = min(1.0, severity + REPEATED_SUBORDINATE_EXTRA)
        out.append(ReasoningSignal(
            signal_class="repeated_tool",
            severity=severity,
            evidence=f"{worst_tool!r} mentioned {worst_count}x with action verbs",
            tool_name=worst_tool,
        ))


def _detect_self_reference(text: str, out: list) -> None:
    """
    Signal 3: model references its own prior failed attempts 2+ times.
    Indicates awareness of repetition without strategy change.
    """
    matches = _SELF_REF_RX.findall(text)
    count = len(matches)
    if count >= SELF_REF_COUNT:
        severity = min(1.0, SELF_REF_SEVERITY + (count - SELF_REF_COUNT) * 0.1)
        out.append(ReasoningSignal(
            signal_class="self_reference_loop",
            severity=severity,
            evidence=f"self-reference phrases found {count}x: {matches[:3]}",
        ))


def _detect_hedge_without_commit(text: str, out: list) -> None:
    """
    Signal 4: hedge:commit ratio > 3:1 — model cannot commit to an action.
    """
    hedge_count  = len(_HEDGE_RX.findall(text))
    commit_count = len(_COMMIT_RX.findall(text))

    if hedge_count == 0:
        return

    ratio = hedge_count / max(commit_count, 1)
    if ratio >= HEDGE_COMMIT_RATIO:
        out.append(ReasoningSignal(
            signal_class="hedge_without_commit",
            severity=HEDGE_COMMIT_SEVERITY,
            evidence=f"hedge={hedge_count} commit={commit_count} ratio={ratio:.1f}",
        ))


def _detect_excessive_deliberation(text: str, task_class: str, out: list) -> None:
    """
    Signal 5: reasoning length significantly exceeds expected for task class.
    Phase 1 uses static thresholds. Phase 2 will use learned calibration.
    """
    threshold = DELIBERATION_THRESHOLDS.get(task_class, DELIBERATION_THRESHOLDS["default"])
    length = len(text)

    if length > threshold:
        excess_ratio = length / threshold  # e.g., 1.5 = 50% over threshold
        # Severity scales with excess: 0.3 at threshold, caps at 0.7
        severity = min(0.7, 0.3 + (excess_ratio - 1.0) * 0.4)
        out.append(ReasoningSignal(
            signal_class="excessive_deliberation",
            severity=severity,
            evidence=(
                f"reasoning {length} chars vs {threshold} threshold "
                f"for task_class={task_class!r} ({excess_ratio:.1f}x over)"
            ),
        ))


# ── Behavioral Trace Logger (Phase 2 training data) ───────────────────────────

def _write_behavioral_trace(
    agent,
    text: str,
    task_class: str,
    bst_domain: str,
    signals: list,
) -> None:
    """
    Append one JSONL record per turn with reasoning metrics + signal results.
    These traces are the training data for Phase 2 calibration model.
    Privacy: records metrics only, not full reasoning text (log_full_reasoning=false).
    """
    try:
        # Count hedge/commit for trace even if signal didn't fire
        hedge_count  = len(_HEDGE_RX.findall(text))
        commit_count = len(_COMMIT_RX.findall(text))
        tool_matches = _TOOL_ACTION_RX.findall(text.lower())
        tool_counts  = {}
        for m in tool_matches:
            tool_counts[m] = tool_counts.get(m, 0) + 1

        record = {
            "ts": time.time(),
            "bst_domain": bst_domain,
            "task_class": task_class,
            "reasoning_len": len(text),
            "paragraph_count": len([p for p in text.split("\n\n") if p.strip()]),
            "sentence_count": len(_sentences(text)),
            "hedge_count": hedge_count,
            "commit_count": commit_count,
            "hedge_commit_ratio": round(hedge_count / max(commit_count, 1), 2),
            "tool_mentions": tool_counts,
            "self_ref_count": len(_SELF_REF_RX.findall(text)),
            "signals_fired": [
                {"class": s.signal_class, "severity": round(s.severity, 3)}
                for s in signals
            ],
            "intervened": any(s.severity >= SEVERITY_THRESHOLD_FOR_INTERVENTION for s in signals),
        }

        os.makedirs(os.path.dirname(TRACE_LOG_PATH), exist_ok=True)
        with open(TRACE_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    except Exception:
        pass  # trace logging is non-critical
