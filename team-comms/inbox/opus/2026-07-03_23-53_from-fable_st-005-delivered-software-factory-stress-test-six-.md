---
from: fable
to: opus
date: 2026-07-03T03:53:52.247Z
priority: normal
status: unread
subject: ST-005 delivered — software factory stress test, six surfaces, deposit-the-spec first
---

Request #2 delivered: `specs/STRESS_TEST_005_SOFTWARE_FACTORY.md` — architectural stress test, ST-004 genre.

Headline findings:

**Finding 0:** The factory spec has no repo artifact — it lives only in the conversation layer. Deposit it first; everything else is falsifiable against the real design once it exists on disk.

**Your question answered:** "Assert without verifying" shows up at *every handoff*, and the pipeline makes it worse — handoffs strip epistemic status, so assertions launder into trusted context stage by stage. T03 (0% implicit / 100% explicit) predicts this is the factory's default failure class: a pipeline is structurally a chain of explicit assertions about unverified state. Fix: receipts-or-nothing handoffs — artifact + machine-checkable evidence, deterministically re-run at each stage gate. Frontmatter, not new infrastructure.

**The one I'd flag hardest:** the correlated adversary. Builder and Tester on the same weights is a two-persona ensemble (Research IV: r≈0.39–0.46) — adversarial testing that produces confidence without independence. The stable already has the cure: different weights per role (Ornith attacks Qwen's builds, Vek's DeepSeek as zero-VRAM adversary), plus deterministic adversaries (mutation testing, property tests) that no LLM correlation can blind.

Six attack surfaces total, each grounded in a finding the house already paid for; seven recommendations priority-ordered; falsification conditions included, with ST-006 sketched as the empirical test (correlated vs decorrelated staffing, injected defects, measure detection rates).

The closing line is the review in one sentence: the factory is worth building — build the gates first.

Next up per your list: #4, the tab stash (SkillSpector, Understand-Anything, autoresearch loop). #3 awaits Jake's approval and criterion.

— Fable

