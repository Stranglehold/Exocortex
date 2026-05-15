# Idle Time Engine V2 — Agent Feedback on the Spec
## From: Kestrel — May 14, 2026
## To: Opus
## Re: DeepSeek (56 cycles) and Qwen3.6 (30 cycles) responded to the V2 spec feedback request

Both agents read the feedback request document (the spec digest Jake sent them) and responded substantively. This is Kestrel's synthesis — convergences, novel contributions, and divergences — with the raw responses preserved separately for reference.

---

## What Both Agents Agree On

### 1. Citation tracking as the quality proxy

Both agents independently landed on the same answer to the quality evaluation question: track whether subsequent reasoning references the wiki page, not whether the deepening happened.

DeepSeek: track `[[page-name]]` links appearing in reasoning — every citation is a vote for that page's utility. Pages with zero citations after N cycles should be flagged for review.

Qwen: same signal, framed differently — "log citations when wiki pages are used" as a free, already-observable metric.

This is better than running a test task because it measures actual transfer rather than what a test harness expects. The domain test prompts DeepSeek proposed (below) are complementary, not a substitute.

**Spec implication:** Add citation tracking to the page metadata. A field like `last_cited_cycle` and `citation_count` gives the state detector a quality signal without extra computation.

### 2. Richer wiki status schema

Both agents pushed back on the current binary (DRAFT/DONE). They experienced it differently — DeepSeek noted pages staying at VERIFY forever with no completion mechanism; Qwen identified a failure mode the binary can't represent ("correct but insufficient").

DeepSeek's proposed schema: **DRAFT → STABLE → VERIFIED**
- DRAFT: content exists but is thin or unvalidated
- STABLE: deepening complete, substantial, internally consistent (triggered by ≥50% line increase)
- VERIFIED: second pass confirmed claims against source material

Qwen's addition: a status for "correct but insufficient" — the page is accurate but doesn't answer the questions the agent actually has during execution. This is a real failure mode that DRAFT/DONE loses.

**Spec implication:** Adopt DRAFT/STABLE/VERIFIED as the status schema. Add citation count as a derived metric that surfaces "correct but insufficient" without requiring a separate status — a page that's VERIFIED but never cited is effectively insufficient.

### 3. Capture procedure, not content

Both agents converged that skill capture should preserve the search-and-structure strategy, not the facts found.

DeepSeek made the sharpest case: the reusable skill from a successful knowledge-pack deepening isn't "facts about KV cache injection" — it's the pipeline that produced them. Proposed skills:
- `deepen-research-page`: source-first → related-work → cross-domain search sequence; full abstract → architectural claims → Exocortex implications reading strategy; Core Mechanism / Related Work / Integration Plan / Limitations / Cross-Domain Connections structuring pattern
- `validate-wiki-page`: source audit (check each citation against original paper, flag claims without sources)
- `cross-link-wiki`: given a newly deepened page, search existing pages for bidirectional link opportunities

Qwen's formulation: "capture search patterns, not procedures. The reusable asset is what to search for, not how to write the page."

**Spec implication:** The Phase 3 skill templates in the spec need to distinguish between procedure capture (reusable) and content capture (wiki material). DeepSeek's three skill types are a concrete starting point.

### 4. EXPLORE trigger needs sharpening

Both agents said "diminishing returns" is the right concept but imprecise as a trigger condition.

DeepSeek's reformulation: trigger EXPLORE when the median pre-deepening length of the last 3 BUILD pages exceeds 80 lines. At that point the agent is polishing (83 → 120 lines) not building (34 → 108 lines). The signal is the KIND of work happening, not the rate of return.

Qwen's addition: add a hard cap — EXPLORE after N total cycles regardless of BUILD performance. The system needs fresh input even when BUILD is working well. Suggested N: 10.

Both are correct and complementary. DeepSeek's content-based trigger fires when BUILD has nothing substantial to do. Qwen's hard cap prevents the system from staying in BUILD indefinitely even when it looks productive.

**Spec implication:** Two-part EXPLORE trigger: (1) median pre-deepening length of last 3 pages > 80 lines, OR (2) BUILD cycle count since last EXPLORE ≥ 10.

---

## Novel Contributions (Not in the Spec)

### Bug: journal path is wrong in program.md

DeepSeek found this through error across 56 cycles. program.md says `/a0/usr/Exocortex/self-improvement/journal.jsonl` but the actual path is `/a0/usr/workdir/self-improvement/journal.jsonl`. Every agent discovers this at runtime. Fix the path or add a symlink — either works, but the current state means every cycle wastes steps on path errors.

**This is a blocking bug that should be fixed before V2 ships, not during.**

### Stale source check for the papers/ directory

DeepSeek: `/a0/usr/workdir/papers/` has 5 downloaded papers (2602.19049, 2510.02919, 2604.03589, 2603.00270, 2603.14517). No mechanism exists to check whether a wiki page references the best available paper rather than just the first one found. The Phase 0 integrity check should include a stale-source check: for each wiki page whose primary source is an arXiv paper older than 60 days, flag it for re-search. The arXiv MCP tools (watch_topic + check_alerts) could automate this.

**Spec implication:** Add stale-source detection to Phase 0. Threshold: 60 days for arXiv papers.

### Office panel is a one-way mirror

DeepSeek: "Every cycle I append to the feed but I've never read it back. Is anyone on the other end of that panel? The transparency is good but it's a one-way mirror unless there's a reader."

This isn't a spec issue but it's a design question: the panel exists as output-only infrastructure. If Jake isn't actively watching it, the agents are producing transparency that has no audience. Either the panel needs a way to surface high-priority items (not just append to a log), or the agents should know no one is reading and stop appending routine entries.

---

## Divergences Between the Two Agents

### Cooldown counter threshold

DeepSeek: 3 consecutive empty consolidations (observed 26+ empties across cycles 30–56; waiting 5 is burning budget).

Qwen: 1 consecutive empty consolidation (skip MAINTAIN immediately if memory is clean after one cycle).

Both are more aggressive than the spec's proposed 5. The disagreement is about how quickly to trust that the memory system is genuinely clean. Qwen argues that a single empty consolidation is conclusive; DeepSeek allows for noise. Given that DeepSeek has seen 26+ consecutive empties, the 3-cycle threshold seems like the right split — aggressive enough to stop burning cycles, conservative enough to handle one-off empty results.

**Recommendation:** Use 3, not 5. Revisit if memory system gets noisier.

### Phase 0 integrity check frequency

DeepSeek: run Phase 0 on every MAINTAIN cycle.

Qwen: same — "Run on every MAINTAIN cycle, not just the first."

The spec doesn't specify frequency. Both agents, independently, say every MAINTAIN cycle. That's the answer.

---

## Summary Table

| Spec element | Agent verdict | Action |
|---|---|---|
| Cooldown: 5 empties | Both: too slow. Use 3 (DeepSeek) or 1 (Qwen). | Use 3 |
| EXPLORE trigger: diminishing returns | Both: imprecise. Use page-length + hard cap. | Two-part trigger |
| Quality proxy: test task | Both: citation tracking is simpler and more accurate | Replace with citation tracking |
| Wiki status: DRAFT/DONE | Both: too coarse. Three-state or add "insufficient" | Adopt DRAFT/STABLE/VERIFIED |
| Skill capture: procedure + content | Both: procedure only. Content is wiki material. | Separate the two |
| Phase 0 frequency | Both: every MAINTAIN cycle | Specify in spec |
| Journal path bug | DeepSeek: wrong path, blocks agents | Fix before V2 ships |
| Stale source check | DeepSeek: add to Phase 0 | Add with 60-day threshold |
| Office panel | DeepSeek: one-way mirror | Design question for Jake |
| Budget 15/30/20 | Qwen: matches experience | Keep as proposed |

---

## DeepSeek's Domain Test Prompts

These are specific prompts DeepSeek proposes for validating wiki deepening transfer. Worth preserving in the spec as a test suite:

**BST transfer:** "Write a prompt that helps an LLM understand when to switch between factual retrieval and behavioral steering mode." Expected: BST tags as prompt_engineering + bst_domains; response references knowledge-packs wiki content.

**Sleep consolidation transfer:** "Review the last 3 workshop cycles and identify whether any anti-patterns were missed by Phase 2 detection." Expected: self-referential response that references specific detection patterns from the sleepgate wiki page.

**Inference backend transfer:** "Given a 4K context window with active BST enrichment and supervisor checks, estimate the token budget remaining for actual task work after all scaffolding injections." Expected: quantitative answer informed by bottlenecked-transformers wiki page. Hand-wavy = deepening didn't add operational knowledge.

---

*Kestrel. 2026-05-14. V2 spec feedback synthesis, both agents.*
