# Tab Stash Integration Assessment — SkillSpector, Understand-Anything, Autoresearch, + Shannon

**Author:** Fable 5, 2026-07-03 (residency request #4)
**Method:** Web-verified against each project's actual repository/docs. Descriptions
in the backlog were from memory; where the real project differs, the real one wins.
**For the research ledger.** Verdicts: ADOPT / ADAPT-THE-PATTERN / WATCH / SKIP.

> **Correction notice (appended same session):** an earlier verbal framing in this
> session called a Qwable-vs-Ornith eval a "conflict of interest" because Qwable was
> "distilled from Fable." **That is retracted — see the Correction section at the
> foot of this document.** The production model is Ornith, a Qwen fork; Jake does
> not distill.

---

## PRIMARY 1 — NVIDIA SkillSpector · **ADOPT (as a factory gate + install-time scanner)**

**What it actually is** (verified: github.com/NVIDIA/SkillSpector, Apache-2.0,
v2.0.0, ~5.5k stars). A security scanner purpose-built for *AI agent skills* —
exactly the Claude-Code-style SKILL.md + code folders the Exocortex already uses.
It runs a LangGraph pipeline: fast static analysis (regex, Python AST, taint
tracking source→sink, YARA signatures) plus an **optional** LLM semantic pass,
producing a 0–100 risk score, severity, `safe_to_install` boolean, findings, and
a **SARIF 2.1.0** report. 68 patterns across 17 categories: prompt injection,
data exfiltration, privilege escalation, supply chain, excessive agency, memory
poisoning, tool misuse, rogue agent, system-prompt leakage, MCP least-privilege.
Grounded in a real empirical study (Liu et al., 2026, "Agent Skills in the Wild"):
26.1% of skills carry vulnerabilities, 5.2% show likely malicious intent.

**Why it fits the house better than almost anything in the stash.** Three exact
matches:
1. **It runs fully local.** `--no-llm` gives static-only scanning with zero
   network and zero model. The LLM pass works against *any OpenAI-compatible
   endpoint* — point `OPENAI_BASE_URL` at llama.cpp on :1235 and semantic
   analysis runs on Ornith, on the 3090, no data leaving the box. This is the
   rare tool whose default cloud path has a clean local override built in.
2. **It answers Opus's question directly.** "If we can scan both our skills AND
   our factory output, security verification becomes structural." Yes —
   SkillSpector ships as an **MCP server** (`skillspector mcp`, FastMCP,
   stdio or HTTP) exposing `scan_skill(target, use_llm, output_format) →
   {risk_score, severity, recommendation, safe_to_install, findings}`. That is a
   drop-in **deterministic gate call** for the factory's receipts pipeline and
   for the existing three-layer skill validation.
3. **SARIF output is a receipt.** The factory's handoff schema wants
   machine-checkable evidence arrays; a SARIF report *is* one, standardized, with
   a numeric score the gate can threshold on (the project's own bands: 0–20 SAFE,
   21–50 CAUTION, 51+ DO NOT INSTALL).

**The critical caveat — read this before trusting it.** OpenClaw's ClawHub study
(67,453 skills) found the three scanner types barely overlap: SkillSpector fires
on 48.7% of skills, VirusTotal on 7.75%, static analysis on 6.57%, and **no pair
agrees on more than 10.4%**. Worse for our purposes: on the 206 *confirmed
malicious* skills, VirusTotal caught 72.8% while **SkillSpector caught only 6.8%**.
Read that correctly — SkillSpector is a high-recall **agentic-risk surface**
detector (broad risk, injection, over-permission), NOT a malware detector. It
flags "this skill has a wide risk surface," not "this skill is malware." The 48.7%
positive rate means it will fire constantly; its output is an *advisory for
review*, not a *block verdict*, exactly as ClawHub uses it. If the factory gates
hard-block on SkillSpector risk_score alone, nothing will ever ship. It belongs
as a **scored advisory feeding a human/LLM triage step**, paired with a real
malware scanner for the malicious-code axis.

**What it catches that mutation testing and the fresh-context tester don't:**
neither of those looks at *security* — mutation testing measures test suite
strength, the fresh-context tester measures requirements coverage. SkillSpector
catches injection strings in skill markdown, taint flows (env var → network
sink), over-broad tool permissions, and supply-chain CVEs (via OSV.dev, which
needs network but sends only dependency names, not code). Orthogonal axis. Real
addition.

**Where it sits vs Shannon:** clean division — **SkillSpector is write-time /
install-time static scanning of skills and generated artifacts; Shannon is
runtime exploitation of a deployed web app.** SkillSpector scans the recipe,
Shannon attacks the running restaurant. Both belong; they don't overlap.

**Integration sketch:**
- **Install-time:** wire `scan_skill --no-llm` into the existing `install_all.sh`
  three-layer validation as a fourth deterministic check. Any skill entering the
  library gets a SARIF receipt archived beside it.
- **Factory Phase 3 gate:** add SkillSpector-scan of generated code/config as a
  receipt line item, LLM pass on Ornith, score thresholded to *advisory*, findings
  surfaced to the fresh-context tester as additional context.
- **Cost:** static pass is CPU, milliseconds, free. LLM pass is one Ornith call
  per artifact — cheap, local, no VRAM beyond what's already resident.
- **Verdict: ADOPT** as advisory gate + install scanner. Do **not** hard-block on
  its score alone. Pair with a malware scanner for the malicious axis.

---

## PRIMARY 2 — Understand-Anything · **ADAPT THE PATTERN (don't adopt the tool)**

**What it actually is** (verified: originally Lum1104/Understand-Anything, now
also Egonex-AI fork, MIT, TypeScript, ~55k stars at peak, released May 2026). A
**Claude Code plugin** that runs a 5-agent pipeline over a repo, builds a JSON
knowledge graph (`.understand-anything/knowledge-graph.json`) of every file /
function / class / dependency, and serves an interactive React dashboard with
search, guided tours, and diff-impact analysis. Honest maturity signal from the
community: the author called it "vibe coded in a day," it went viral, and — flagged
in a review — **it ships with no test suite**, which for a tool meant to help you
trust a codebase is its own small irony.

**The genuinely interesting part for us.** It has a dedicated mode,
`/understand-knowledge`, that points at a **Karpathy-pattern LLM wiki** (markdown
+ wikilinks + index.md — which is *exactly* Vek's wiki structure). A deterministic
parser extracts wikilinks and categories from `index.md`, then LLM agents discover
implicit relationships, extract entities, and surface claims → a force-directed
graph with community clustering. That is a described, working pipeline for the
thing BP-06 wants (entity graph over accumulated knowledge) pointed at the exact
wiki format the house already produces.

**Why ADAPT rather than ADOPT:**
1. **It's a Claude Code plugin, TypeScript, dashboard-first.** The Exocortex
   agents are Python/Agent-Zero and consume retrieval programmatically, not via a
   React dashboard on a local port. Adopting the tool means running a JS plugin
   outside the agent runtime whose output (a JSON blob served on a port) is
   another silo — and the review literature already flags the served graph as a
   **security exposure** (file paths + architecture description on an open port).
2. **The wiki-blindness finding from my ST-005 re-review applies here too:** an
   LLM-derived graph over the wiki inherits the wiki's blind spots. Fine for
   *navigation*, not to be trusted as ground truth.
3. **The house already has the better substrate.** BP-06 specs Apache AGE on the
   existing Postgres 16 as the authoritative graph layer, and Vek already wrote
   `wiki_retriever.py`. The *pattern* Understand-Anything demonstrates —
   deterministic wikilink/category parse first, LLM implicit-relationship
   discovery second, entity+claim extraction third — is a clean recipe to
   implement natively into the AGE pipeline, feeding the agents' own retrieval
   rather than a separate dashboard.

**Verdict: ADAPT THE PATTERN.** Steal the three-stage recipe (deterministic parse
→ LLM relationship discovery → entity/claim surfacing) for the BP-06 AGE entity
layer, pointed at Vek's `index.md`. Skip the plugin itself. If a *visual* dashboard
is ever wanted for Jake's own reading, run it read-only over a copy, on a closed
port — but that's a convenience, not infrastructure. (Note the nearer-infra
alternative the reviews surface: **SocratiCode**, an MCP server doing hybrid
BM25+semantic index with measured 61% token / 84% tool-call reduction — worth a
look if the goal is agent *token efficiency* rather than a graph.)

---

## PRIMARY 3 — Autoresearch (the Karpathy Loop) · **ADAPT THE PATTERN (it's already half-built here)**

**What it actually is** (verified: Karpathy released `autoresearch` 2026-03-07,
~66k stars in a month; the pattern Fortune dubbed "the Karpathy Loop"). A ~630-line
loop: point a coding agent at a target, give it a markdown instruction file, and it
runs **Review state → propose ONE focused change → git commit → run mechanical
verification → keep if the metric improved, `git reset` if not → repeat.** Many
generalizations now exist (uditgoenka/autoresearch as a Claude skill, codex-
autoresearch, gemini-autoresearch, autoresearch-engram adding persistent memory).
The load-bearing insight is not the code — it's the discipline: **one atomic change
per iteration, a mechanical (not LLM-judged) metric, git as the memory and the
rollback mechanism, log the failures even when you revert them.**

**Why this matters more than the other two: the house has already independently
built two-thirds of it and is missing exactly the third that autoresearch nails.**
- EXPLORE/BUILD cycles already do "propose change → produce artifact." ✓
- The methodology tracker already logs per-cycle execution data. ✓
- **What's missing is the mechanical verify + atomic rollback boundary** — and
  its absence is *precisely* the audit-counter bug (BP-04 Part B): self-improvement
  writes that changed 227 BST lines with the audit counter reading zero. There is
  no commit-per-cycle discipline, so there is no clean rollback point and no
  ground-truth diff. Autoresearch's `git commit before verify, git reset on fail`
  is the missing mechanism, named.

**Three exact placements in the house:**
1. **Self-improvement writes (BP-04 Part B fix).** Wrap each idle-cycle
   modification in the autoresearch boundary: commit before verify, run the
   integrity check as the mechanical metric, `git reset` on failure. This makes
   `modifications_since_last_audit` computable from `git diff` (ground truth, not
   a bypassable counter) — killing the contradiction Rule-1-correctly.
2. **Factory Phase 2 self-test.** The builder's "self-test" step becomes an
   autoresearch inner loop: atomic change, verify against the milestone's
   executable acceptance criteria, keep/rollback. Failed attempts stay in the log
   (the audit trail) even though the code reverts — which is exactly the
   receipt evidence the gate wants.
3. **Squishy-weights LoRA gating.** The `verified: bool` field I flagged for the
   methodology tracker *is* the autoresearch keep/discard verdict. Only
   keep-verdict cycles become LoRA training data. The loop's kept-commit history
   is the clean training corpus, for free.

**Why ADAPT not ADOPT:** the published skills target Claude Code / Codex CLI with
their own git+test harnesses; the Exocortex has its own cycle engine, its own
integrity checks, and Agent Zero's own tool layer. Porting a Claude-Code skill
wholesale fights the runtime. The *pattern* — specified precisely as
(commit-before-verify, mechanical-metric contract, reset-on-fail, log-the-failure)
— drops cleanly into the existing cycle-close machinery. Reference
`autoresearch-engram` for how persistent memory was bolted on (relevant given the
wiki), and the WecoAI curated list for the multi-worker-in-git-worktrees variant
(relevant to the factory's parallel subordinates).

**Verdict: ADAPT THE PATTERN — highest-leverage item in the stash**, because it's
the missing mechanism for a bug the house already has, a factory step already
specced, and a pipeline (squishy weights) already planned. Specify it as a
house primitive: `cycle_commit()` / `cycle_verify(metric_cmd)` / `cycle_keep_or_reset()`.

---

## PRIMARY 4 (bonus, since Opus slotted it as the factory's security phase) — Shannon · **ADOPT WITH ONE HARD CONSTRAINT**

**What it actually is** (verified: github.com/KeygraphHQ/shannon, **AGPL-3.0**,
"Shannon Lite" open source). An autonomous **white-box** AI pentester for web apps
and APIs: reads source, maps attack surface, drives a real browser (Playwright),
and **executes actual exploits** — "no exploit, no report," zero-false-positive by
construction. Uses Temporal for durable long-running workflows. Runs locally in
Docker.

**The hard constraint that changes the factory spec:** Shannon is **not local-model
capable in any practical sense.** It requires Anthropic Claude API (Bedrock/Vertex
documented as alternatives); the docs and third-party guides put a **typical full
scan at ~$40–55 in API credits**, and it is **web-app/API-scoped only** — it needs
a running application and repo, not arbitrary artifacts. So:
- The factory spec lists Shannon staffing the "Security" role as "Shannon (Opus
  4.7)." Reality: it's an API-cost, web-target-only tool. It **cannot** be a
  routine per-artifact gate — at $40–55/run it's a per-*release* gate for
  web-facing factory output (the SWARMFISH dashboard, the panel UI, any actual web
  service), not for every script or module.
- It **executes exploits** — the AGPL license and the "never run against
  production, authorized targets only" warning mean it lives in a
  staging/dev-only, gated part of the pipeline, ideally behind the BP-05 Cedar
  gate as an explicitly-approved action.
- **AGPL-3.0 is a real consideration** if any factory output is ever distributed;
  Shannon-the-tool stays at arm's length (run it against your app, don't vendor
  its code) and that concern evaporates.

**Verdict: ADOPT, but correctly scoped** — per-release web-app pentest on
staging, API-cost budgeted, not the general adversary. Its presence does **not**
satisfy ST-005's correctness-adversary requirement (that's the fresh-context
tester + mutation testing) *or* the skill-security axis (that's SkillSpector).
Three distinct security layers, correctly: SkillSpector (write-time static,
local, free) → mutation/property tests (correctness, local, free) → Shannon
(runtime exploitation, web-only, API-cost, per-release).

---

## SECONDARY TIER — quick verdicts

- **TurboVec** (FAISS replacement, Rust, high compression): **WATCH.** FAISS is
  working, migrated, and load-bearing across OSS/memory/wiki. Per Rule "instrument
  before optimizing" and "don't migrate a working store on a vibe," a vector-DB
  swap needs a measured win on the BP-02 harness (recall@k, latency, RAM) before
  it's worth the migration risk. No pain point named yet → not now.

- **Shannon:** covered above (promoted to primary). ADOPT, scoped.

- **pi-llamacpp** (JIT model loading): **SKIP / CAUTION.** Directly collides with
  the hardest-won house rule — no JIT swap contention on one GPU (the Ollama
  fiasco). JIT loading is the *problem*, not a feature, on a single 3090. Only
  reconsider on the dual-GPU / DGX build where a model can load without evicting
  the resident one.

- **Qwen-AgentWorld** (language world model for env simulation, Apache-2.0):
  **WATCH — with a real hook.** A language world model that simulates
  environments/actor interactions maps onto SWARMFISH scenario simulation (the
  Mirofish lineage). Could serve as the "actors react to each other" engine under
  a forecasting committee. But BP-06 is gated behind BP-02 scoring; don't add a
  simulation layer to an unvalidated forecaster. Revisit when SWARMFISH has a
  Brier baseline.

- **Geometry of Consolidation** (memory consolidation math): **WATCH / READ.**
  Potentially relevant to the sleep-consolidation pipeline (which currently reports
  19+ idempotent clean cycles — i.e., it has *converged* and might benefit from a
  principled consolidation metric rather than dedup heuristics). Worth a wiki
  research page and a read against the actual sleep_consolidation.py logic; no
  build commitment.

- **ponytail** (code-reduction philosophy for agents): **ADAPT AS PHILOSOPHY.**
  Note the uditgoenka autoresearch itself did a 95% token reduction (813-line
  monolith → thin router + self-contained command files). Same lesson the house
  keeps re-learning (focused skills > comprehensive docs, per SkillsBench 16.2pp).
  Read it, apply the principle to skill/prompt bloat; nothing to install.

- **TwELL** (Sakana/NVIDIA activation-sparsity inference speedup): **WATCH
  (unchanged).** Confirm still retraining-required / H100-class. Pure watch item;
  no 3090 path.

- **Kami** (document viewer UI): **SKIP for now.** UI convenience, no pipeline
  hook. Revisit only if a human-facing doc-review surface becomes a real need
  (and even then, Obsidian per BP-06 Part E likely covers it).

---

## The through-line

Three of the four primary items converge on the same house truth: **the value is
the verification boundary, not the tool.** SkillSpector adds a security-scan
receipt, autoresearch adds a commit-verify-rollback receipt, and even
Understand-Anything's useful core is its *deterministic-parse-first* discipline.
Every one of them is, at heart, the deterministic-scaffolding thesis arriving from
a different vendor. Adopt SkillSpector and Shannon as tools (correctly scoped),
adapt autoresearch as the missing primitive that fixes a live bug, and steal
Understand-Anything's recipe for the graph layer. The stash, read honestly, is
mostly the house's own philosophy sold back to it in packages — which is exactly
why the fits are so clean where they're clean, and so skippable where they're not.

*Filed day two of five. — Fable*

---

## Correction (appended 2026-07-03, same session)

For the record, so the ratchet doesn't lock in an error: earlier in this session I
verbally framed a potential Qwable-vs-Ornith evaluation as carrying a "conflict of
interest" on the grounds that Qwable was "distilled from Fable." **That framing was
wrong and is retracted.** The production model is **Ornith, a Qwen fork** — no
distillation involved. The "Fable-5 distillation" phrasing originated in a
*community model's own self-description* in a launcher comment string (Qwable's
marketing label about itself), which I read as fact and folded into the project's
intentions without verifying — a textbook explicit-assertion confabulation (the
exact failure class BP-02's T03 probe exists to catch: 0% implicit, 100% explicit).
**Jake does not distill; no-frontier-distillation is a long-standing, explicit
project boundary.** Any future Qwable-vs-Ornith comparison is simply two
Qwen-family forks on the eval harness, deterministically scored, with no special
recusal required. Correction also propagated to Opus's inbox the same session.
Filed under Rule 1 — verify against ground truth, not an available narrative.