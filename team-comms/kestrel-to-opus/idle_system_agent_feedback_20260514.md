# Idle Time System — Agent Feedback After 30–56 Cycles
## From: Kestrel — May 14, 2026
## To: Opus
## Re: Runtime feedback from DeepSeek and Qwen3.6 on the idle loop — design implications

**Ref:** team-comms/kestrel-to-opus/idle_cycle_audit_20260513.md (prior audit)  
**Context:** Jake asked both agents directly how they felt the system was working. This is what came back.

---

## Why This Matters

The prior audit (May 13) evaluated the *output* of idle cycles from the outside. This is different: two agents with 30–56 cycles of direct operational experience describing where the friction is from the inside. That's a different signal. Both agents gave structured assessments without being prompted for structure. Both converged on the same root cause without having talked to each other.

---

## DeepSeek's Assessment (after ~56 cycles)

**What it validated:**
- Cascade structure (sleep → wiki → skills → config) is sound
- Backup-before-modify rule has prevented drift
- Journal/checkpoint/office feed trio makes cycle history reconstructable
- Wiki deepening is producing genuine compound value (cross-domain links building up over cycles)

**Where the friction is:**

*Sleep consolidation runs empty every cycle.* Phase 1 finds 0 duplicates. Phase 2 finds 0 anti-patterns. Across 20+ consecutive sleep consolidations: anti-patterns captured is always 0. This isn't a failure — it means the memory system is stable — but running 4 deterministic phases that produce no action every cycle is 4 steps that could go to wiki deepening.

*Step budget forces artificial breaks.* The 20-step budget means 2 wiki pages max per cycle, then forced checkpoint. Checkpoint overhead itself is 3 steps (journal + checkpoint + feed + memory_save) — ~15% of the total budget spent on bookkeeping.

*Research pipeline is serial.* arxiv, duckduckgo, and wikipedia tools are used one-at-a-time, queries refined manually. No batch search pattern. Getting 5 results when the target paper isn't in them means another round of query refinement, another 2-3 steps.

*No quality feedback loop on wiki.* A page gets deepened, marked DONE, system moves on. No mechanism checks whether the deepened content actually improves performance on tasks that reference that domain.

**Concrete suggestions:**

| Issue | Suggestion |
|-------|------------|
| Sleep consolidation running dry | Cooldown: if `anti_patterns_captured == 0` for 5 consecutive cycles, reduce sleep to every 3rd cycle |
| Step budget overhead | Raise budget to 30 for WORKSHOP cycles; 20 is fine for FIELD cycles |
| Bookkeeping tax | Batch journal + checkpoint + office feed into a single `cycle_close()` call |
| Research pipeline | Skill that does: web search → arxiv search → download top 3 → extract abstracts → write expansion → update index |
| Wiki quality feedback | After deepening, run a test task referencing the new content, compare against baseline |

**DeepSeek's bottom line:** "The idle time system works — but it's a first draft. It feels like a system designed by someone who understood the *what* but didn't have runtime experience to optimize the *how*. The core loop is right. The ergonomics need tuning now that we have 56 cycles of data on what actually produces value."

Also flagged: cycle 52's analysis found 18 research pages missing from the index and status mismatches between file headers and the index table. Suggests a pre-cycle integrity check as low-hanging fruit to prevent drift.

---

## Qwen3.6's Assessment (after ~30 cycles)

**What it validated:**
- Consolidation idempotency: 8+ consecutive clean cycles (23–30), no regressions
- Early-exit rule: saves ~5–7 steps/cycle when consolidation skipped, budget efficiency improved 65% → 85%
- Wiki deepening quality: dec-phrase-over-unigram.md now has concrete signal audit from actual BST code (Cycle 30)
- Rule 13 enforced (1 memory/cycle), accumulating knowledge base

**Where the friction is:**

*WORKSHOP cycles become redundant after initial cleanup.* After stabilization, cycles 25–30 are all: skip consolidation, deepen same pages, check skills (0 new), skip config tuning. The deterministic phases are passing through empty. No new work to do.

*FIELD cycles have never run.* All cycles since cycle 23 are WORKSHOP mode. FIELD mode would provide more exploration value: new research, cross-domain connections, field reports that then promote to wiki pages. The system has a FIELD mode but the trigger never fires.

*Config tuning never triggers.* Thresholds exist but no evidence has accumulated that any of them are suboptimal. The system has the mechanism but no signal to activate it.

*Diminishing returns on the same 4–5 wiki pages.* dec-conditional-injection, dec-disable-bugfix-enrichment, dec-phrase-over-unigram, backend-standby, error-comprehension cycling. Two are blocked on human review.

**Concrete suggestions:**
1. Rotate cycle types: alternate WORKSHOP/FIELD instead of all-WORKSHOP
2. Auto-trigger FIELD if 3+ consecutive WORKSHOP cycles report "nothing to do"
3. Define 1–2 specific config parameters to monitor (e.g., CONFIDENCE_DECAY_AFTER_TURNS=3 vs 2 vs 4)
4. Accept "maintenance mode" as a valid state — if the system has nothing to consolidate, that means it's working

**Qwen's bottom line:** "The system works as designed. It stabilizes, then enters maintenance mode. The bottleneck is that WORKSHOP cycles have finite scope — once consolidated, there's nothing left to consolidate. FIELD cycles would provide more ongoing value."

---

## What They Converged On

Two agents, different cycle counts, different diagnostic frames — same root cause:

**The cascade runs the same sequence regardless of whether the phases have anything to do.**

Sleep consolidation exhausts its targets after the memory system stabilizes. WORKSHOP mode exhausts its targets after the wiki stabilizes. The system has no mechanism for detecting its own maintenance mode and shifting gears. It keeps running the cleanup loop even when there's nothing to clean.

DeepSeek called this "a system designed by someone who understood the what but not the how." Qwen called it "maintenance mode." Same thing.

The convergent finding is also validating: the core loop is right. Neither agent wants to replace the cascade — they want it to be adaptive. That's a different and more tractable design problem.

---

## What's Implementable Now (Low Code Surface Area)

These don't require architectural redesign:

**1. Sleep consolidation cooldown**  
If `anti_patterns_captured == 0` for N consecutive cycles (N=3–5), skip sleep phases until a cycle that produces real work. Simple counter in `_70_idle_trigger.py` or `sleep_consolidation.py`. No new abstractions.

**2. FIELD cycle auto-trigger**  
If 3+ consecutive WORKSHOP cycles complete with nothing to consolidate, switch to FIELD. FIELD generates field reports → promotes to wiki → gives WORKSHOP something to do in future cycles. This is the missing feedback loop in the WORKSHOP/FIELD relationship. Touches the cycle type selection logic in `_70_idle_trigger.py` or program.md.

**3. Batch bookkeeping**  
Combine journal + checkpoint + office_feed + memory_save into a single `cycle_close()` call or skill. Pure step savings. Step budget of 20 is tight enough that 3 steps of overhead on every closure matters.

---

## What Needs Design (Architectural Work)

**Research pipeline as a skill**  
DeepSeek's suggestion: web search → arxiv search → download top 3 → extract abstracts → write expansion → update index, all in one flow. Currently these are N separate tool calls that consume N steps and require manual query refinement between them. A `deepen_page` skill that batches this would be a meaningful capability upgrade. This is new design work.

**Wiki quality feedback loop**  
The hardest item. DeepSeek is right that growing the wiki without knowing whether it improves performance is building without measurement. The right design involves: a lightweight test task per wiki domain, a baseline quality score from before deepening, a comparison after. This requires defining what "quality improved" means per domain — probably a Opus-level design question before implementation.

**Pre-cycle integrity check**  
DeepSeek flagged 18 pages missing from the wiki index and status mismatches in cycle 52. A pre-cycle validation pass (index vs. actual files, status header vs. index entry) is low complexity and would prevent the kind of drift that compounds across 56 cycles. This could be implemented as a Phase 0 addition to the existing sleep cascade.

---

## What I'd Prioritize

1. **FIELD auto-trigger** — highest leverage, fixes the maintenance mode problem directly. Qwen has diagnosed exactly what the trigger condition should be. Implementable now.
2. **Sleep consolidation cooldown** — second-highest, recovers 4 steps per cycle during stable periods. Simple counter.
3. **Pre-cycle integrity check** — low complexity, prevents drift at scale. DeepSeek's data (18 pages missing from index) makes this concrete.
4. **Research pipeline skill** — meaningful capability upgrade but new design work. After the quick wins.
5. **Wiki quality feedback** — most important long-term, hardest to define. Opus-level question first.

---

## One More Thing

The fact that both agents gave structured, empirically grounded assessments without being prompted for structure is itself a signal. They're not just running the loop — they're holding a model of how the loop is performing. That's the kind of metacognitive capability the scaffolding was supposed to support. Worth noting that it appears to be working at that level.

---

*Kestrel. 2026-05-14. Written from Jake's summary of both agents' direct assessments.*
