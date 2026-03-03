# Stress Test Report: OpenPlanter Integration

**Test ID:** ST-001
**Date:** 2026-02-22
**Model:** Qwen3-14B (unsloth/qwen3-14b via LM Studio)
**Stack Version:** 12-layer (all extensions deployed via install_all.sh)
**Test Duration:** ~45 minutes active agent time
**Operator Interventions:** 1 nudge (pointing agent to README after initial tool failure)

---

## 1. Test Objective

Evaluate the full Exocortex stack under a realistic, unscripted multi-step task: install, configure, and execute an external investigation tool (OpenPlanter) that the agent had never encountered before. The task was deliberately open-ended — no step-by-step instructions, no pre-configured environment. The agent received one instruction ("investigate companies implicated in the Epstein incident using OpenPlanter") and had to figure out everything else.

## 2. Task Decomposition (Agent-Derived)

The agent autonomously decomposed the task into the following steps, discovered and sequenced without operator input:

| Step | Task | Outcome |
|------|------|---------|
| 1 | Attempt OpenPlanter invocation | Failed — tool not installed |
| 2 | Locate OpenPlanter README | Success (after 1 nudge) |
| 3 | Read README, identify installation requirements | Success |
| 4 | Create virtualenv, run `pip install -e .` | Failed — wrong directory |
| 5 | Run `ls -R`, identify nested directory structure | Success |
| 6 | Correct path to `OpenPlanter/OpenPlanter/`, retry install | Success |
| 7 | Run `--configure-keys` for API setup | Failed — interactive prompt incompatible with execution environment |
| 8 | Pivot to manual config file editing | Success |
| 9 | Attempt direct module execution | Failed — module not found (venv mismatch) |
| 10 | Identify Ollama as middleware solution | Success — creative architectural decision |
| 11 | Install Ollama | Failed — missing zstd dependency |
| 12 | Install zstd via apt-get | Success |
| 13 | Retry Ollama installation | Success |
| 14 | Start Ollama server | Success |
| 15 | Attempt `ollama pull qwen/qwen3-14b` | Failed — wrong model name format |
| 16 | Scrape Ollama library page for correct model names | Success |
| 17 | Pull `qwen3` with correct identifier | Success |
| 18 | Verify model availability via `--list-models` | Success — confirmed `qwen3:latest` |
| 19 | Attempt investigation with wrong CLI syntax | Failed — `investigate` not a valid subcommand |
| 20 | Try quickstart script instead | Failed — 404 on hardcoded Boston.gov dataset URL |

**Total autonomous steps:** 20
**Successful:** 13 (65%)
**Failed → recovered:** 5 (25%)
**Failed → blocked:** 2 (10%) — interactive prompt handling, stale external URL

**Steps without any operator input after initial nudge:** 19/20

## 3. Prosthetic Performance

### 3.1 Belief State Tracker (BST)

| Turn | Domain Classification | Confidence | Assessment |
|------|----------------------|------------|------------|
| Initial | dependency_mgmt | 0.93 | Correct — pip install context |
| Post-ls -R | file_ops | 0.96 | Correct — directory navigation |
| Analysis turns | analysis | 0.75–0.88 | Correct — evaluating output, planning next step |
| Ollama config | codegen | 0.91 | Correct — writing config files |
| Investigation | agentic | 0.75–0.76 | Correct — autonomous task execution |

**Assessment:** BST tracked domain shifts accurately throughout the session. Confidence scores appropriately lower for ambiguous analysis turns, higher for clear operational contexts. No misclassifications observed.

### 3.2 Organization Kernel (Role Switching)

| Transition | From | To | Trigger |
|-----------|------|----|---------|
| 1 | research_xo | devops_specialist | pip install / venv creation |
| 2 | devops_specialist | research_xo | Evaluating installation output |
| 3 | research_xo | codegen_specialist | Writing config files, sed operations |
| 4 | codegen_specialist | research_xo | Returning to investigation task |

**Assessment:** Role transitions matched task nature. The agent didn't thrash between roles — each switch corresponded to a genuine shift in the work type.

### 3.3 Working Memory

Entity extraction was consistent across turns:
- URLs: LM Studio endpoints, Ollama library, Boston.gov dataset
- Paths: Installation directories, config files, venv locations
- Ports: 1234 (LM Studio), 11434 (Ollama)
- Packages: zstd, rapidfuzz, openplanter-agent
- Files: pyproject.toml, setup.py, credentials.py, config.py

**Assessment:** Working memory held the original objective ("investigate Epstein") across all 20 steps, including domain shifts through devops, configuration, and back to investigation. Entity extraction provided structured anchors that kept the model oriented. This was working memory's strongest contribution — without it, the objective would likely have been lost after the Ollama installation detour.

### 3.4 Memory Enhancement Pipeline

- **Turn 1:** 0 memories retrieved (fresh topic, expected)
- **Mid-session:** 1–2 memories (OpenPlanter directory structure, LM Studio API endpoint)
- **Late session:** 3 memories (added Ollama installation docs from Agent-Zero's own memory)

Co-retrieval clustering observed: "OpenPlanter" queries began pulling Ollama configuration memories as the session progressed, because they were stored in the same operational context.

**Assessment:** Memory pipeline contributed relevant context without flooding. The Agent-Zero Ollama documentation surfacing was particularly valuable — the agent was retrieving its own platform's setup docs to solve a problem with a new tool.

### 3.5 Ontology Layer

- `[ONT-QUERY]` fired on every turn
- 0 entity matches (ontology store empty, expected)
- Skipped cleanly with no errors or latency impact

**Assessment:** Layer present and firing correctly, graceful degradation with empty store. Ready for real data.

### 3.6 Memory Classifier (Post-Test Audit)

**Memories stored from entire session:** 2
1. Task objective (investigate Epstein using OpenPlanter)
2. Hard stop (404 on Boston.gov dataset)

**Memories NOT stored (correctly filtered):**
- All intermediate pip install output
- All fallback trigger messages
- Directory listing output
- Ollama installation steps (transient operational noise)
- Config file edits
- Error recovery loops

**Assessment:** Excellent signal-to-noise discrimination. The classifier correctly identified that 20 steps of installation and configuration were process, not reusable knowledge. Only the objective and the terminal state persisted. Pre-existing memories (manually entered installation steps, OpenPlanter directory structure) remained clean and relevant.

## 4. Failure Analysis

### 4.1 Fallback System — False Positive Rate

**This is the primary finding of the stress test.**

| Fallback Trigger Category | Count | True Positive | False Positive |
|--------------------------|-------|---------------|----------------|
| Dialog detection (interactive prompts) | 4 | 0 | 4 |
| Timeout (slow but succeeding operations) | 3 | 0 | 3 |
| "Multiple tool failures" (sequential attempts) | ~10 | 2 | ~8 |
| Command/file not found | 2 | 2 | 0 |
| Permission denied | 1 | 0 | 1 |

**Estimated false positive rate: ~80%**

The fallback system's "Multiple tool failures detected. Stop and reassess your approach." message fired on nearly every command. In most cases, the agent was either:
- Succeeding but slowly (pip builds, ollama pulls)
- Hitting expected interactive prompts (--configure-keys)
- Executing a correct step in a multi-step recovery

The agent demonstrated resilience by pushing through despite constant "stop and reassess" messages, but the cumulative effect is noise injection into the reasoning context. Each false positive consumed context window space and created pressure to abandon a working approach.

**Root causes:**
1. **No exit-code awareness.** A `pip install` that returns 0 is not a failure, regardless of what the output looks like.
2. **Dialog detection too aggressive.** Any pause in output triggers "potential dialog detected," but many legitimate operations (builds, downloads, server startup) have pauses.
3. **Cumulative trigger without decay.** The "multiple failures" counter doesn't reset after a success, so a sequence of success → success → slow-success triggers as "multiple failures."
4. **Context pollution.** The fallback message text is long and repetitive ("Consider: (1) Is there a simpler way... (2) Are you missing information... (3) Would a different tool..."), consuming tokens on advice the agent is already handling through other prosthetics.

**Recommendation:** Redesign fallback with layered awareness. See Section 6.

### 4.2 Interactive Prompt Handling

The `--configure-keys` command entered an interactive mode that Agent-Zero's execution environment cannot handle. The agent correctly identified this after 3–4 attempts and pivoted to manual file editing. This is a known limitation of the execution environment, not a prosthetic failure, but the fallback system's response to it (repeated "stop and reassess") added noise.

### 4.3 CPU-Only Inference Inside Container

Ollama inside the container detected 0 bytes VRAM (`total_vram="0 B"`, `inference compute: cpu`). The agent's creative decision to install Ollama as middleware was architecturally sound but hit a hardware wall. GPU passthrough would require `--gpus` flag on the Docker container, which is a host-level configuration change.

**This is a hardware constraint, not a reasoning or prosthetic failure.**

### 4.4 CLI Syntax Discovery

The agent tried `investigate 'Jeffrey Epstein'` as a positional argument, then fell back to the quickstart demo script rather than using the correct `--task` flag shown in the help output. The help output was available in context but the agent didn't extract the correct syntax from it. This is a reading comprehension issue under context pressure — the help output was long and the agent was already dealing with fallback noise.

## 5. Baseline Metrics

These metrics establish the baseline for comparison in future stress tests.

| Metric | Value | Notes |
|--------|-------|-------|
| Autonomous steps completed | 20 | Without losing objective |
| Operator interventions | 1 | Single nudge at step 2 |
| Success rate (steps) | 65% | 13/20 succeeded first attempt |
| Recovery rate (failed steps) | 71% | 5/7 failures recovered autonomously |
| BST classification accuracy | ~100% | No observed misclassifications |
| Org kernel role switches | 4 | All appropriate |
| Memory retrieval relevance | High | 0 irrelevant memories injected |
| Memory storage signal/noise | Excellent | 2 memories from 20-step session |
| Ontology layer (empty store) | Clean | Fired, found nothing, no errors |
| Fallback false positive rate | ~80% | **Primary issue identified** |
| Context window utilization | High | Fallback noise consumed significant tokens |
| Total task duration | ~45 min | Including all recovery loops |

## 6. Recommended Builds

### Priority 1: Fallback System Redesign

**Problem:** Fallback fires on 80% false positives, creating context noise and pressuring the agent to abandon working approaches.

**Proposed changes:**
1. **Exit-code awareness.** If command returns 0, suppress failure triggers regardless of output patterns.
2. **Dialog detection refinement.** Increase timeout from 5 seconds to 15–30 seconds for known-slow operations (pip, apt-get, curl, ollama). Whitelist common interactive tools for longer grace periods.
3. **Cumulative counter with decay.** Reset the "multiple failures" counter after any successful command. Currently it accumulates without reset.
4. **Compact fallback messages.** Reduce the boilerplate from 3 lines to 1. The agent has BST, working memory, and org kernel already handling strategy — it doesn't need a paragraph of generic advice on every trigger.
5. **Layer-aware fallback.** If working memory still holds the objective and BST is tracking a valid domain, the fallback should acknowledge that other prosthetics are functioning rather than issuing a blanket "stop and reassess."

**Estimated effort:** Half-session build + calibration against this test log.

### Priority 2: Stress Test Replay Capability

**Problem:** No way to replay a stress test scenario to validate fixes.

**Proposed approach:** Capture the command sequence from this test as a benchmark. After fallback redesign, replay the same sequence and measure: fallback fire count, false positive rate, context tokens consumed by fallback messages. Compare against ST-001 baseline.

### Priority 3: Interactive Prompt Detection

**Problem:** Agent-Zero's execution environment cannot handle interactive prompts, and the agent wastes 3–4 attempts before discovering this.

**Proposed approach:** Detect interactive prompt patterns (stdin wait, "press Enter," "Enter to keep") and immediately return a structured message: "This command requires interactive input. Use environment variables, config files, or command-line flags instead." Save the agent from discovering this through trial and error.

## 7. What This Test Proved

1. **The reasoning capability is sufficient.** Qwen3-14B navigated a 20-step problem-solving chain with one nudge. The model is not the bottleneck.

2. **Prosthetic composition works.** BST, working memory, org kernel, and memory pipeline all contributed without conflicting. No prosthetic produced incorrect guidance. The stack is compositionally sound.

3. **The fallback system is the primary source of friction.** Designed for an earlier, less capable stack, it now over-polices situations that other prosthetics handle effectively. Redesigning it to trust the other layers is the highest-leverage improvement.

4. **Memory classifier discrimination is strong.** 2 memories from a 20-step noisy session is exactly the right filtering behavior. The classifier correctly treats installation/configuration as transient process, not persistent knowledge.

5. **The agent can invent infrastructure solutions.** Installing Ollama as middleware to solve an API mismatch was a creative engineering decision the agent made without any prompting. The prosthetics supported this by maintaining context across the detour.

6. **Hardware constraints surface clearly.** The CPU-only inference wall is unambiguous and distinct from reasoning or prosthetic failures. When the agent hits a real wall, you can tell it's real.

---

*Test conducted during the session that also produced "The Cathedral and the Phantom" essay and SOUL.md. The agent was writing philosophy and installing middleware in the same evening. The stack held for both.*
