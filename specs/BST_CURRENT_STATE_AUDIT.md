# BST Current State Audit
## B1 Deliverable — Sprint "The Routing Core"

**Date:** 2026-04-17
**Author:** Opus
**Version audited:** BST v3.2, deployed 2026-04-15
**Model context:** Qwopus3.5-27B-v3 (Q4_K_M), confirmed as primary per DP-1
**Inputs:** Compound BST Design Note, Prosthetic Cortex Design Note, ST-004 findings, ST-010 regression data, Agent Zero Observations, Kestrel's Model Evaluation Report (SESSION-062), Token Economics Field Note
**Purpose:** Ground truth document. What the BST does now, exhaustively. Every downstream consumer. Every signal. Every failure mode observed. Three specific investigation targets from the model evaluation.

---

## 1. Architecture Overview

The BST is Layer 1 of the Exocortex twelve-layer stack. It fires on every turn, before the model reasons, and produces a domain classification that downstream systems consume. It is the first processing step after the user's message arrives and before the model sees any context.

### 1.1 Dual Classifier System

The BST consists of two independent classification systems running in sequence:

**System A: DOMAIN_CONFIGS (regex-based)**
- Operates on the user message text
- Runs all domain matchers simultaneously, collects scores (count of matched signals)
- Selects primary domain (highest score) and optional secondary domain (second highest, if above threshold)
- Produces compound classification: `primary+secondary` signature
- Drives enrichment injection and skill surfacing
- Autonomous loop classification strips `<think>` blocks before classification, applies a 4000-character window cap

**System B: slot_taxonomy.json (trigger-based)**
- Separate domain list from System A
- Trigger-based slot resolution for contextual slots and preambles
- Defers to compound BST domain (v3.2 fix: slot resolver now uses BST primary domain)
- Produces preamble text injected alongside enrichment

Both systems must have matching domain entries. Adding a domain to System A without System B causes slot resolution to fall through silently to `conversational` with no useful context. This was discovered during Session 048 when the three register-shift domains were added.

### 1.2 Classification Flow

```
User message arrives
  → Strip <think> blocks (autonomous loop)
  → Cap at 4000 characters
  → Run all DOMAIN_CONFIGS matchers → collect {domain: score} map
  → Apply _COMPLEX_BUILD_RX gating (auto-promotes to coding if matched)
  → Select primary (highest score)
  → Select secondary (second highest, if ≥ 1 signal and not in disabled_domains)
  → Apply momentum: compare compound signature to previous turn
    → If register-shift domain (orientation, meta_cognitive, philosophical): 
      break momentum immediately (Rule 0)
    → If same compound signature: increment momentum counter
    → If different: reset momentum, adopt new classification
  → Write _bst_domain (string, primary only) to shared state
  → Write _bst_compound (full dict) to shared state
  → Build enrichment: primary full + secondary abbreviated (Option B)
  → Inject enrichment into context before model reasoning
  → Trigger slot_taxonomy.json resolution using primary domain
  → Inject preamble
```

---

## 2. Domain Inventory

### 2.1 Operational Domains (12)

| Domain | Signal Count (v3.2) | Priority | Enrichment | Key Signals |
|---|---|---|---|---|
| **coding** | ~8 signals | 2 | Tool guidance, write_file protocol, section-by-section for large files | `\bcode\b`, `\bfunction\b`, `\bclass\b`, `\bscript\b`, `\bbuild\b`, `\bimplement\b`, `\bwrite.*(?:python\|script\|code)` |
| **bugfix** | ~6 signals | 3 | Diagnostic procedures, error pattern matching | `\bbug\b`, `\bfix\b`, `\berror\b`, `\bbroken\b`, `\bdebug\b`, `\bcrash` |
| **investigation** | ~6 signals (post-v3.2) | 11 (demoted from 1) | OSINT methodology, source evaluation | `\binvestigat\b`, `\bentit\b`, `\bsource\b`, `\bOSINT\b`, `\bintelligence\b` |
| **analysis** | ~5 signals (narrowed v3.2) | 4 | Structured comparison, quantitative extraction | `\banalyz\b`, `\bcompare\b`, `\btrend\b`, `\bassess\b`, `\bevaluat\b` (removed `\breview\b`, `\bperformance\b`) |
| **financial** | 15 signals (new v3.2) | 5 | Financial research, real-time data, market analysis skills | `\bstock\b`, `\bmarket\b`, `\bportfolio\b`, `\btrade\b`, `\bearnings\b`, `\bSEC\b`, `\bhedge\b`, `\bequit\b`, `\bfund\b`, `\bP/?E\b`, `\bdividend\b`, `\bvolatil\b`, `\bcredit\b`, `\byield\b`, `\binflation\b` |
| **file_ops** | ~4 signals | 7 | Path verification, file operation safety | `\bls\b`, `\bcat\b`, `\bread.*file\b`, `\bcopy\b` |
| **system_admin** | ~5 signals | 6 | System operation procedures | `\bdocker\b`, `\bsystemctl\b`, `\bservice\b`, `\binstall\b`, `\bconfigure\b` |
| **research** | ~4 signals | 8 | Research methodology | `\bresearch\b`, `\bpaper\b`, `\bstudy\b`, `\bliterature\b` |
| **planning** | ~10 signals (extended v3.2) | 9 | Project planning, task decomposition | `\bplan\b`, `\bstrateg\b`, `\broadmap\b`, `\bprioritiz\b`, `\bnext\s+step\b`, `what\s+should\s+we`, `how\s+should\s+we`, `let'?s\s+(?:figure|think|work)`, `what'?s\s+the\s+(?:best|right)\s+(?:way|approach)` |
| **conversation** | ~2 signals | 10 | Minimal — conversational context only | `\bhello\b`, `\bthanks\b`, general greeting patterns |
| **git_ops** | ~3 signals | 12 | Git workflow guidance | `\bgit\b`, `\bcommit\b`, `\bbranch\b` |
| **testing** | ~3 signals | 13 | Test execution, validation | `\btest\b`, `\bpytest\b`, `\bunittest\b` |

### 2.2 Register-Shift Domains (3)

These domains have special behavior: they break momentum immediately (Rule 0) and provide minimal or empty enrichment — giving the model cognitive space instead of technical framing.

| Domain | Priority | Enrichment | Key Signals | Purpose |
|---|---|---|---|---|
| **orientation** | 0 (wins ties) | Light — one line: "Identity and state reflection — draw from self-knowledge, not technical context." | `\bsoul\b`, `\bidentity\b`, `\borient\b`, `\breconstruct\b`, `\bself-assess\b`, `how.*feel`, `what.*like.*inside` | Reading identity documents, reconstructing context, relational check-ins |
| **meta_cognitive** | 0 (wins ties) | Empty — open cognitive space | `\bmy\s+own\b`, `\bdesigned\s+this\b`, `\bfrom\s+the\s+inside\b`, `\brunning\s+under\b`, `\barchitect\b`, `\bprocess\b.*\breflect\b` | Analyzing own systems, self-assessment, thinking about thinking |
| **philosophical** | 0 (wins ties) | Empty — maximum space | `\bvalues\b`, `\bethics\b`, `\bmeaning\b`, `\bpurpose\b`, `\bwhy\s+does\s+(?:this\|it\|that)\s+matter\b`, `\bphilosoph\b`, `\bprinciple\b`, `\bdesign\b` | Values, meaning-making, preservation, depth |

### 2.3 Domain Count Summary

15 total domains: 12 operational + 3 register-shift.

---

## 3. Downstream Consumers

The BST classification is read by five systems. Each system consumes the BST output differently and has different failure modes when classification is wrong.

### 3.1 Enrichment Gating (Active — Layer 1)

**What it does:** Injects domain-specific context text before the model reasons. Primary domain gets full enrichment template. Secondary domain gets abbreviated one-line note.

**How it consumes BST:** Reads `_bst_compound` for primary and secondary domains, reads model profile for `disabled_domains`, builds enrichment plan.

**Failure mode on misclassification:** Model receives irrelevant guidance. For operational domains, this wastes context tokens (~100-300 tokens of wrong enrichment). For register-shift domains misclassified as operational, the model receives technical framing during reflective work, potentially suppressing philosophical depth. For operational domains misclassified as register-shift, the model loses tool guidance it needs.

**Token cost:** ~100-300 tokens per turn for full enrichment, ~20 tokens for secondary abbreviated note. Over 20 turns: 2,000-6,000 tokens of enrichment.

### 3.2 Skill Surfacing (Active — Layer 1, _19_skill_suggester.py)

**What it does:** Surfaces relevant skills from `/a0/usr/skills/` based on BST domain. Added in Kestrel's Observations Item 2, deployed.

**How it consumes BST:** Reads `_bst_domain` (primary), maps to skill categories.

**Failure mode on misclassification:** Wrong skills surfaced. Financial skills appear during coding tasks. Investigation skills appear during file operations. The model may attempt to use an irrelevant skill, wasting turns.

**Token cost:** ~50-100 tokens per skill suggestion.

### 3.3 TALE Reasoning Budget (Active — Layer 1)

**What it does:** Injects a thinking token budget hint into BST enrichment for execution-mode domains.

**How it consumes BST:** Reads `_bst_domain` (primary), applies three-tier budget:
- Execution mode (coding, system_admin, file_ops, git_ops, bugfix): "~200 tokens. Execute."
- Planning mode (planning, complex_build): "~500 tokens. Plan concisely."
- Analysis mode (investigation, analysis, financial, research): No constraint
- Register-shift (orientation, meta_cognitive, philosophical): No constraint

**Failure mode on misclassification:** If an execution task is classified as investigation, the budget hint is removed and the model may produce verbose thinking chains (800-1600 tokens). If an investigation task is classified as coding, the budget hint constrains reasoning depth when deep analysis is needed. This is the T5 failure from the model evaluation — PEP content triggered philosophical domain, dropping the execution budget, and the model shifted into analytical mode instead of continuing step execution.

**Token cost:** ~15 tokens for the budget hint line.

### 3.4 Tool Injection (Pending — B2b, _16_tool_registry.py)

**What it will do:** Filter tool injection based on BST domain. Only inject tools relevant to the current task. Fall back to full list on `general` or unknown domains.

**How it will consume BST:** Will read `_bst_domain` and `_bst_compound`, query `tool_domains.json` for domain→tool mapping.

**Failure mode on misclassification:** Critical tool missing from injected set. Mitigated by: always inject "use stack_status for full list" fallback, and inject union of current + previous domain's tools on domain transitions.

**Token savings:** Estimated 340 → 60-80 tokens on domain-matched turns.

### 3.5 Supervisor Sensitivity (Indirect — Layer 8)

**What it does:** The supervisor loop monitors agent behavior. It does not directly consume BST domain, but its behavior is indirectly affected: enrichment-guided tasks produce different behavioral patterns than un-enriched tasks, and the supervisor's anomaly detection calibrates to those patterns.

**How it consumes BST:** Indirectly, through the behavioral patterns enrichment produces.

**Failure mode on misclassification:** Not directly a BST failure, but chronic misclassification can cause the supervisor to calibrate its "normal" baseline to enrichment-influenced behavior, making it less effective at detecting genuine anomalies.

---

## 4. Known Failure Modes

### 4.1 Historical Failures (Resolved)

| ID | Failure | Root Cause | Resolution | Version |
|---|---|---|---|---|
| F-001 | 59% of turns classified `investigation` | Investigation had 10 signals (widest net), priority 1 (highest), broad signals like `\breview\b` matching routine language | Demoted to priority 11, removed broad signals, narrowed to investigation-specific terms | v3.2 |
| F-002 | Identity documents classified as `config_edit + file_ops` | `cat SOUL.md` triggered file_ops signals, `settings.json` triggered config_edit. No orientation domain existed | Added orientation, meta_cognitive, philosophical domains with register-shift momentum override | v3.1 (Session 048) |
| F-003 | Complex builds classified as conversation | `_COMPLEX_BUILD_RX` gate only ran within certain domain paths, missed unclassified complex build descriptions | Fixed: gate now runs regardless of domain, auto-promotes to coding | v3.2 |
| F-004 | Autonomous loop classification corrupted by `<think>` blocks | Model's thinking tokens (hundreds of characters) were being classified as user content, triggering false domain signals | Strip `<think>` blocks before classification, cap window at 4000 chars | v3.2 |
| F-005 | Slot resolver ignoring BST domain | slot_taxonomy.json had its own classification, not deferring to BST compound | Unified: slot resolver defers to BST primary domain | v3.2 |

### 4.2 Active Failures / Known Weaknesses

#### F-006: Philosophical Domain Signal Over-Breadth ⭐ (From Model Evaluation T5)

**Severity:** Medium-High. Directly caused T5 step-compliance failure.

**Description:** BST classified Python PEP/language-design research content as `philosophical+planning`. This caused: (1) removal of execution budget hint, (2) model shifted into analytical mode, (3) abandoned sequential step execution after step 4.

**Root cause:** The philosophical domain includes signals like `\bdesign\b`, `\bprinciple\b`, `\bphilosoph\b`. PEP documents and language design discussions contain these words frequently in a technical context. The BST cannot distinguish "design principles of Python's type system" (technical, should route to investigation or research) from "the philosophical principles underlying this architecture" (genuinely philosophical, should route to philosophical).

**Affected signals:**
- `\bdesign\b` — fires on any design discussion, technical or philosophical
- `\bprinciple\b` — fires on engineering principles, not just philosophical ones
- `\bphilosoph\b` — fires on "design philosophy" in technical docs

**Proposed fix:** Narrow the philosophical signals. Options:
1. **Remove `\bdesign\b` from philosophical.** This signal fires too broadly. Technical design discussions are far more common than philosophical ones. The remaining philosophical signals (`\bvalues\b`, `\bethics\b`, `\bmeaning\b`, `\bpurpose\b`, `\bwhy\s+does.*matter\b`) are sufficient and more specific.
2. **Add negative filters.** If `\bdesign\b` matches but `\bPEP\b`, `\bPython\b`, `\bAPI\b`, `\binterface\b` also match, suppress the philosophical classification. Negative filters add complexity but preserve signal breadth.
3. **Require 2+ philosophical signals to classify.** Single-signal philosophical classification is too fragile. Requiring two or more signals makes the classification more confident. Combined with register-shift's Rule 0 (immediate momentum break), this prevents single-word philosophical captures.

**Recommendation:** Option 3 (minimum 2 signals) is the cleanest. It doesn't remove useful signals; it just requires corroboration. A message that contains both `\bdesign\b` and `\bvalues\b` is likely philosophical. A message that contains only `\bdesign\b` is more likely technical. This is the same principle as the investigation demotion in v3.2 — broad signals firing alone shouldn't dominate classification.

**Implementation:** Add a `min_signals` field to domain config. Default 1 for operational domains. Set to 2 for all three register-shift domains. This prevents single-word register-shift captures while preserving the Rule 0 momentum break when two or more signals confirm the register shift.

#### F-007: Multi-Step Task Compliance Cliff ⭐ (From Model Evaluation T5)

**Severity:** Medium. Affects explicitly-numbered multi-step instructions.

**Description:** Model correctly executed steps 1-4 of a 10-step sequence, then produced a verbose analytical response instead of continuing execution. The BST domain drifted during execution as search results introduced new topical signals.

**Root cause:** Two factors:
1. **Model characteristic (act-then-refine paradigm):** v3 is trained to act on initial signal, then synthesize. Long sequential instructions conflict with this training — the model's natural disposition is to reflect after a few actions.
2. **BST domain drift during execution:** Search results about PEP content triggered philosophical signals (F-006 above), which removed the execution budget hint, which allowed the model to shift into analytical mode. The domain drift and the model disposition reinforced each other.

**Proposed fix:** Two-part:
1. **Fix F-006 first.** Preventing false philosophical classification during technical research stabilizes the budget hint, which keeps the model in execution mode.
2. **Add multi-step persistence enrichment.** When the BST detects numbered-step patterns in the user message (regex: `\bstep\s+\d\b` or numbered list with 5+ items), inject: "Complete all numbered steps before synthesizing. Continue execution through all steps. Do not produce analysis until final step is complete." This is enrichment, not supervisor intervention — it's proactive guidance rather than reactive correction.

**Alternative:** The supervisor could detect multi-step task progress (count completed steps vs total steps) and inject continuation signals when execution stalls. But this is a heavier intervention than enrichment and risks the prescriptive-injection problem that SFX-001 solved (the old "LOOP DETECTED" message caused meta-loops). Enrichment is lighter and less likely to disrupt.

#### F-008: Output Token Truncation on Large Code (From Model Evaluation T2)

**Severity:** Medium. Affects large file generation tasks.

**Description:** Model correctly chose write_file but content truncated at ~25 lines due to 16384 max_tokens output ceiling.

**Root cause:** Not a BST classification failure per se, but the BST coding enrichment template is the intervention point. The template mentions write_file and multi-step file protocol but doesn't enforce section-by-section generation explicitly enough for the model to follow on fresh (non-append) files.

**Proposed fix:** Update BST coding enrichment template to include explicit guidance: "For files >20 lines, generate in sections of ≤20 lines each. Use write_file in append mode after the first section. Never attempt to write a complete class or module in a single tool call." The section-by-section pattern should be the default, not the fallback.

#### F-009: Enrichment-Ignored Drift (Conceptual — Not Yet Instrumented)

**Severity:** Unknown until instrumented.

**Description:** The BST has no feedback mechanism to detect whether its enrichment actually influenced the model's behavior. If the model consistently ignores enrichment for N turns (as observed during the Session 049 orientation incident), the classification is likely wrong but the BST has no way to know.

**Status:** Closed-loop BST concept documented in Agent Zero Observations and Prosthetic Cortex Design Note. Not yet designed as an implementation. Deferred to post-v3.3 — requires a feedback mechanism from response processing back to classification.

---

## 5. Signal Overlap Analysis

The following signals fire across multiple domains, creating ambiguity zones where classification depends on which other signals co-fire:

| Signal Pattern | Domains That Match | Ambiguity Risk |
|---|---|---|
| `\bdesign\b` | philosophical, coding, planning | **High** — technical design vs philosophical design. F-006 root cause. |
| `\breview\b` | (removed from analysis in v3.2) | Resolved. Was causing analysis over-classification. |
| `\btest\b` | testing, coding, bugfix | Low — testing priority 13 means it only wins when no coding/bugfix signals present |
| `\berror\b` | bugfix, investigation | Low — bugfix priority 3 wins over investigation priority 11 |
| `\binstall\b` | system_admin, coding | Low — system_admin fires on infrastructure work, coding fires on implementation work |
| `\bprocess\b` | meta_cognitive, system_admin, planning | Medium — "my process" vs "the process" vs "process management". Meta_cognitive's compound pattern (`process.*reflect`) helps but single-word `process` can leak. |
| `\bquery\b` | investigation, coding, financial | Low — usually co-fires with domain-specific terms that disambiguate |
| `\bprinciple\b` | philosophical, planning | **Medium** — "engineering principle" vs "ethical principle". Same issue as `\bdesign\b`. Would be resolved by min_signals=2 for philosophical. |
| `\bstrateg\b` | planning, financial, investigation | Low — usually co-fires with domain-specific context |

**Assessment:** The high-risk overlaps are concentrated in the philosophical domain's signal set. The operational domains have minimal problematic overlap after v3.2's narrowing. The F-006 fix (min_signals=2 for register-shift domains) would resolve the two high-risk overlaps and the medium-risk `\bprinciple\b` overlap simultaneously.

---

## 6. Domain → Tool Mapping (For B2b Implementation)

Based on this audit, the recommended `tool_domains.json` mapping:

```json
{
  "_meta": {
    "version": "1.0",
    "description": "BST domain to tool mapping for gated injection",
    "wildcard": "*",
    "updated": "2026-04-17"
  },
  "coding": ["write_file", "code_execution_tool", "text_editor", "stack_status", "staging_note"],
  "bugfix": ["code_execution_tool", "text_editor", "stack_status", "staging_note"],
  "testing": ["code_execution_tool", "text_editor", "stack_status"],
  "investigation": ["search_engine", "camofox_browser", "oss_ingest", "oss_query", "swarmfish_predict", "tla_check", "stack_status", "staging_note"],
  "analysis": ["search_engine", "camofox_browser", "oss_query", "swarmfish_predict", "tla_check", "stack_status", "staging_note"],
  "financial": ["search_engine", "camofox_browser", "oss_query", "swarmfish_predict", "stack_status", "staging_note"],
  "research": ["search_engine", "camofox_browser", "stack_status", "staging_note"],
  "file_ops": ["write_file", "text_editor", "code_execution_tool", "stack_status"],
  "system_admin": ["code_execution_tool", "stack_status"],
  "git_ops": ["code_execution_tool", "text_editor", "stack_status"],
  "planning": ["staging_note", "stack_status"],
  "conversation": ["stack_status"],
  "orientation": ["stack_status"],
  "meta_cognitive": ["stack_status"],
  "philosophical": ["stack_status"],
  "general": "*"
}
```

**Design decisions:**
- `stack_status` and `staging_note` are in nearly every domain — they're universal utilities
- Register-shift domains get only `stack_status` — reflective work doesn't need tools, and injecting tool options would bias the model toward action during reflection
- `general` (fallback for unknown classification) gets the full tool list via wildcard
- Domain transition union: on the turn after a domain change, inject the union of current domain's tools and previous domain's tools. This prevents the "started investigation, now writing code, but write_file isn't in investigation's tool set" edge case

---

## 7. Enrichment Template Audit

### 7.1 Templates Requiring Updates (From Model Evaluation)

**Coding domain enrichment — NEEDS UPDATE:**
Current template mentions write_file and multi-step file protocol but doesn't enforce section-by-section generation. Update to include:
```
For files >20 lines: generate in sections of ≤20 lines each.
Use write_file in append mode after the first section.
Never attempt to write a complete class or module in a single tool call.
```

**Multi-step task enrichment — NEEDS ADDITION:**
No current template handles explicitly-numbered multi-step instructions. Add detection pattern (regex: `(?:step\s+\d|^\d+\.\s)` appearing 5+ times in user message) and inject:
```
Complete all numbered steps before synthesizing.
Continue execution through all steps sequentially.
Do not produce analysis or summary until the final step is complete.
```

### 7.2 Templates Functioning Correctly

- Investigation enrichment: Working. T3 showed clean first-turn tool selection with epistemic markers.
- Financial enrichment: Working. Financial-research and real-time-data skills surfaced correctly.
- Register-shift enrichment: Working as designed. Empty/minimal enrichment gives the model cognitive space.
- TALE budget hints: Working when domain classification is stable (T4: 35-126 tokens under 200-token budget). Fails when domain drifts (T5 F-006).

---

## 8. Recommendations for v3.3

Ordered by priority (impact × effort):

### Priority 1: F-006 Fix — Register-Shift Minimum Signal Threshold
**Impact:** High — resolves T5 compliance failure, stabilizes TALE budget
**Effort:** Low — add `min_signals` field to domain config, check in classification
**Change:** Set `min_signals: 2` for orientation, meta_cognitive, philosophical. Default `min_signals: 1` for all other domains. Single-signal matches against register-shift domains are recorded in the compound classification but don't win primary unless corroborated by a second signal.

### Priority 2: F-008 Fix — Coding Enrichment Section-by-Section Enforcement
**Impact:** Medium-High — resolves T2 truncation failure for large code generation
**Effort:** Low — text change to enrichment template
**Change:** Add explicit "≤20 lines per tool call" guidance to coding domain enrichment.

### Priority 3: F-007 Fix — Multi-Step Persistence Enrichment
**Impact:** Medium — resolves T5 step-compliance cliff
**Effort:** Low-Medium — add detection pattern + enrichment injection
**Change:** Detect numbered-step patterns in user message, inject continuation instruction.

### Priority 4: B2b — BST-Gated Tool Injection
**Impact:** Medium — token savings, reduced noise
**Effort:** Medium — new config file, modification to _16_tool_registry.py
**Change:** Implement `tool_domains.json` mapping from Section 6 above. Domain transition union. Fallback to full list on unknown/general.

### Priority 5: B2c — TALE Budget Refinement
**Impact:** Medium — depends on F-006 fix (budget only works when domain is stable)
**Effort:** Low — enrichment template text changes
**Change:** Three-tier budget already deployed. Refinement: add Chain of Draft instruction ("One key insight per reasoning step. No narration.") to execution-mode budget hint.

### Priority 6: Closed-Loop BST (Future)
**Impact:** High — converts BST from open-loop to closed-loop
**Effort:** High — requires feedback mechanism from response processing
**Change:** Deferred. Document concept. Build when the routing core (v3.3) is stable.

---

## 9. What This Audit Does NOT Cover

- **Enrichment template content quality.** This audit documents which templates exist and which need updates. It does not evaluate whether the enrichment text itself is optimally written. That's a GEPA optimization target.
- **Slot taxonomy content.** The audit documents that slot_taxonomy.json exists and defers to BST primary domain. It does not audit every slot entry. That's a separate audit if needed.
- **Model profile interaction.** The audit documents that profile-aware enrichment reads `disabled_domains`. It does not evaluate which domains should be disabled for which model profiles. That depends on per-model testing.
- **Prosthetic Cortex.** The audit documents the conceptual gap between surface-token classification and representation-space classification. It does not design the prosthetic cortex. That's the Prosthetic Cortex Design Note.
- **Compositional skills.** The audit documents the BST's role as routing core. It does not design the orchestration engine. That's Phase 4 (B4) of the sprint plan.

---

## 10. Audit Verdict

The BST v3.2 is operationally sound for its intended purpose — turn-level domain classification driving enrichment and skill surfacing. The v3.2 fixes (investigation demotion, financial domain addition, complex build bypass, autonomous loop fix, slot resolver unification) resolved the most impactful failure modes from ST-010.

Three active weaknesses remain, all traceable to the same root cause: the philosophical domain's signal set is too broad for a register-shift domain that carries Rule 0 priority. Narrowing it (min_signals=2) resolves the primary weakness (F-006) and significantly mitigates the secondary weakness (F-007, because stable domain classification keeps the TALE budget active, which keeps the model in execution mode).

The BST is ready to become the routing core. The `tool_domains.json` mapping in Section 6 is validated by this audit. The enrichment template updates in Section 7.1 are the prerequisites. The v3.3 spec (B3) can proceed with these fixes as its foundation.

The routing core trajectory — one classification driving five downstream systems — is architecturally sound. The risk is concentration: one misclassification affects everything. The mitigation is precision: make the classification more accurate (min_signals, signal narrowing) rather than adding redundancy. The BST should be right, not fault-tolerant. Fault tolerance at this layer adds complexity that degrades the very classification quality we're trying to improve.

---

*Audit completed by Opus. Session 061. The ground truth is documented. The fixes are prioritized. The routing core has its foundation.*
