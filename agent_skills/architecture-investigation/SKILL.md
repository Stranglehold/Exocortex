---
name: "architecture-investigation"
description: "Systematic methodology for investigating agent framework architectures, identifying key components, and comparing design patterns across systems. Use when analyzing new frameworks or conducting architectural assessments."
author: "agent"
---
# Architecture Investigation Methodology

## Purpose
Provides a systematic approach for investigating agent framework architectures, identifying key components (context management, memory systems, tool orchestration), and comparing design patterns across different systems.

## When to Use
- When encountering a new agent framework or system
- When conducting architectural assessments for peers
- When comparing multiple frameworks for feature analysis
- When documenting architectural decisions and tradeoffs
## EXECUTION GUARDRAILS (Phase 1 Self-Improvement)

### Before Tool Selection — Quick Checklist:
- [ ] Have I considered the `response` tool for simple reporting?
- [ ] Am I stuck repeating the same approach? If yes, pivot immediately.
- [ ] What would success look like in measurable terms?

### Loop Detection Self-Check:
- **Rule:** If same tool called 2+ times with similar args → STOP and reassess
- **Action:** Use `response` tool to report partial progress when uncertain
- **Pivot:** Try a fundamentally different approach (different tool, simpler method, or ask for guidance)

### Empirical Validation Requirement:
Before stating performance metrics:
1. Define measurement method explicitly
2. Establish baseline for comparison
3. Run actual benchmark, not theoretical estimate
4. Report format: "X% improvement measured via [method] against [baseline]"

**Example:**
- ❌ "80-90% token reduction expected"
- ✅ "Gist-only retrieval uses 156 tokens vs 1,247 for full content (87% reduction) — measured on Helios analysis dataset"
## EMPIRICAL VALIDATION FRAMEWORK (Phase 2 Self-Improvement)

### Core Principles

**1. Measurability First**: Every claim must be backed by measurable data collected through defined methods.

**2. Baseline Required**: No improvement can be claimed without establishing a baseline for comparison.

**3. Statistical Rigor**: Results should include confidence intervals or standard deviations when sample size permits (n ≥ 5).

**4. Reproducibility**: All measurements must document exact conditions, tools, and parameters used.

---

### Validation Protocol by Claim Type

#### Performance Claims (Speed, Efficiency, Token Reduction)

**Required Elements:**
1. **Baseline measurement** — Original state before improvement
2. **Test measurement** — State after improvement  
3. **Sample size** — Number of trials (minimum 3, recommended 5-10)
4. **Statistical summary** — Mean ± standard deviation, or range if n < 5
5. **Conditions documented** — Environment, inputs, parameters held constant

**Report Format:**
```
[X]% improvement in [metric] measured via [method]
Baseline: [value] ± [std_dev or range] (n=[sample_size])
After: [value] ± [std_dev or range] (n=[sample_size])
Conditions: [key parameters held constant]
```

**Example:**
```
87% token reduction in memory retrieval measured via character count comparison
Baseline: 1,247 chars ± 234 (range: 1,013-1,481) for full content retrieval (n=5)
After: 156 chars ± 12 (range: 144-168) for gist-only retrieval (n=5)
Conditions: Same Helios analysis dataset, identical query patterns
```

---

#### Accuracy/Quality Claims

**Required Elements:**
1. **Evaluation criteria** — Clear definition of what constitutes success/correctness
2. **Test set** — Representative sample of cases evaluated
3. **Success rate** — Percentage or count of successful outcomes
4. **Failure analysis** — Brief description of failure modes if any

**Report Format:**
```
[X]% accuracy on [task] evaluated against [criteria]
Test set: [description and size]
Successful: [count]/[total] ([percentage])%
Failure modes: [brief description]
```

---

#### Comparative Claims (A vs B)

**Required Elements:**
1. **Controlled variables** — What was held constant between comparisons
2. **Independent variable** — What differed between A and B
3. **Measurement metric** — How difference was quantified
4. **Effect size** — Magnitude of observed difference

**Report Format:**
```
[Method A] outperformed [Method B] by [X]% on [metric]
Controlled: [list of held-constant variables]
Varied: [independent variable]
A result: [value], B result: [value]
```

---

### Measurement Tools & Methods

#### Token/Character Counting
```python
# For text-based measurements
char_count = len(text_string)
estimated_tokens = char_count / 4  # Rough estimate for English text
```

#### Timing Measurements
```python
import time
start = time.perf_counter()
# ... operation ...
duration_ms = (time.perf_counter() - start) * 1000
```

#### Statistical Summary (for n ≥ 5)
```python
import statistics
data = [trial_1, trial_2, trial_3, trial_4, trial_5]
mean = statistics.mean(data)
stdev = statistics.stdev(data) if len(data) > 1 else 0
report = f"{mean:.1f} ± {stdev:.1f} (n={len(data)})"
```

---

### Reproducibility Checklist

Before reporting results, verify:
- [ ] Baseline measurement documented with exact values
- [ ] Test conditions fully specified (inputs, environment, parameters)
- [ ] Measurement method clearly described
- [ ] Sample size adequate for claim type (n ≥ 3 minimum)
- [ ] Raw data available for verification if requested
- [ ] Statistical measures appropriate for sample size

---

### Common Pitfalls to Avoid

| Pitfall | Example | Correction |
Theoretical claims | "Expected 80% reduction" | Run actual measurement first |
| Single trial | One timing measurement | Minimum 3 trials, report range or std dev |
| Missing baseline | "Now takes 2 seconds" | Include before: "Reduced from 10s to 2s" |
| Vague metrics | "Significantly faster" | Quantify: "5.2x faster (10.4s → 2.0s)" |
| Uncontrolled variables | Different inputs for comparison | Hold all variables constant except tested one |

---

### Quick Reference: Claim Validation Matrix

| Claim Type | Min Sample Size | Required Stats | Report Format |
 Performance improvement | n=3 | Range or mean±stdev | "% change, baseline→after" |
| Accuracy/quality | n=1 per case | Success rate | "X/Y successful (Z%)" |
| Comparative (A vs B) | n=3 each | Effect size | "A: X, B: Y, difference Z%" |
| Bug fix verification | n=1 sufficient | Before/after state | "Fixed: [description]" |

---

### Integration with Execution Guardrails

**Before making any performance claim:**
1. Check guardrails — have I measured or am I theorizing?
2. If measuring — follow appropriate protocol above
3. Report using prescribed format with all required elements
4. Include reproducibility checklist verification

## TOOL SELECTION HEURISTICS (Phase 3 Self-Improvement)

### Quick Decision Tree

**START: What is the investigation goal?**

```
├── Understand codebase structure?
│   ├── Large repo (>10k lines)? → browser_agent + search_engine for overview
│   ├── Medium repo? → document_query on README, then targeted file reads
│   └── Small repo? → Direct document_query on key files
│
├── Find specific feature/implementation?
│   ├── Know approximate location? → document_query directly
│   ├── Need to search first? → search_engine for external context, then browser_agent
│   └── Looking for patterns? → Multiple document_queries with pattern matching
│
├── Compare architectures?
│   ├── 2-3 systems? → Parallel browser_agent sessions
│   ├── Many systems? → search_engine + summary comparison table
│   └── Deep dive needed? → Sequential browser_agent with note-taking
│
├── Answer specific question?
│   ├── Factual/lookup? → response tool directly (if known)
│   ├── Requires research? → search_engine first, then document_query
│   └── Complex analysis? → Break into subtasks, use multiple tools
│
└── Report findings?
    ├── Simple answer? → response tool immediately
    ├── Needs verification? → Quick document_query confirmation
    └── Complex report? → Gather data first, then structured response
```

---

### Tool Selection Matrix by Task Type

| Task | Primary Tool | Secondary Tool | Fallback |
 Search/Discovery | search_engine | browser_agent | document_query |
| Code Reading | document_query | browser_agent | code_execution_tool |
| Architecture Analysis | browser_agent | document_query | search_engine |
| Comparison | browser_agent (parallel) | search_engine | response with caveats |
| Quick Answer | response | search_engine | N/A |
| Complex Investigation | Multiple (sequential) | browser_agent | call_subordinate |

---

### Heuristics for Faster Decisions

#### Rule 1: The 30-Second Test
**If you can answer in <30 seconds from memory → use `response` tool immediately.**

Examples:
- "What is the purpose of the architecture-investigation skill?" → response
- "Explain the gist/content pattern" → response
- "List Helios core components" → response (if recently analyzed)

#### Rule 2: Single Source vs. Multiple Sources
**One source needed?**
- Known file/location → `document_query`
- Unknown but searchable → `search_engine` then `browser_agent`

**Multiple sources needed?**
- Related repos/files → Parallel `browser_agent` sessions or sequential `document_query`
- Web research + code analysis → `search_engine` → `browser_agent` → `document_query`

#### Rule 3: Depth vs. Breadth Tradeoff
| Goal | Approach | Tools |
 Broad overview | Shallow, many sources | search_engine + quick browser_agent scans |
| Deep understanding | Single source, thorough | document_query on key files + analysis |
| Balanced | 2-3 sources, medium depth | browser_agent on READMEs + docs |

#### Rule 4: Tool Cost Awareness
**Fastest to slowest (roughly):**
1. `response` — Instant, no external call
2. `document_query` — Single file read (~2-5 seconds)
3. `search_engine` — Web search (~3-8 seconds)
4. `browser_agent` — Browser session + navigation (~10-30+ seconds)
5. `call_subordinate` — Full agent spawn (~30+ seconds)

**Heuristic:** Start with fastest tool that can reasonably solve the task.

---

### Common Scenario Playbooks

#### Scenario A: "Analyze this GitHub repo's architecture"
```
1. search_engine: "repo-name github" → Get URL and context
2. browser_agent: Navigate to repo, read README, explore structure
3. document_query: Key files (package.json, main entry points)
4. response: Structured summary with components, patterns, tradeoffs
```

#### Scenario B: "Compare framework X vs framework Y"
```
1. browser_agent (parallel or sequential): Read both READMEs and docs
2. Extract: Core architecture, key features, design patterns
3. Compare: Side-by-side analysis table
4. response: Structured comparison with recommendations
```

#### Scenario C: "How does feature Z work in system X?"
```
1. search_engine: Quick context on feature + system
2. browser_agent: Navigate to relevant docs/code
3. document_query: Specific implementation files if needed
4. response: Explanation with code examples if available
```

---

### Tool Selection Checklist (Run in <5 seconds)

Before selecting a tool, answer:

1. **What do I need?** [Facts / Analysis / Comparison / Exploration]
2. **Where is the info?** [Memory / Single file / Multiple files / Web]
3. **How deep?** [Surface / Medium / Deep dive]
4. **Time budget?** [Fast <30s / Medium <2min / Deep >2min]

**Then select:**
- Memory + Facts → `response`
- Single file + Any depth → `document_query`
- Web + Surface/Medium → `search_engine` then `browser_agent`
- Multiple sources + Deep → `browser_agent` sessions or `call_subordinate`

---

### Anti-Patterns to Avoid

| Anti-Pattern | Example | Better Approach |
 Over-researching simple questions | search_engine for "what is REST" | response directly |
| Browser when document suffices | browser_agent for single file read | document_query |
| Sequential when parallel works | One-by-one repo analysis | Parallel browser_agent sessions |
| Ignoring search results | Not using search_engine context | Read snippets before deciding next step |
| Subordinate for simple tasks | call_subordinate for single query | Direct tool use |

---

### Integration with Other Phases

**Before Tool Selection:**
1. Check **Execution Guardrails (Phase 1)** — Am I looping?
2. Apply **Tool Selection Heuristics (Phase 3)** — What's the right tool?
3. After execution, apply **Empirical Validation (Phase 2)** if making claims

**Decision Flow:**
```
Task arrives → Guardrails check (looping?) → Tool selection heuristics 
→ Execute tool → Validate results → Report with empirical backing
```

## MEMORY INTEGRATION PATTERN (Phase 4 Self-Improvement)

### Core Philosophy

**Memory is a force multiplier, not a crutch.** Use it to avoid reinventing solutions, but verify retrieved information against current context.

---

### Memory Usage Decision Tree

**START: Do I need prior knowledge?**

```
├── Have I done similar work before?
│   ├── Yes → memory_load with specific query
│   └── No → Skip to external research (search_engine/browser_agent)
│
├── Is this a repeatable pattern?
│   ├── Architecture analysis patterns → Check memory for frameworks analyzed
│   ├── Tool selection heuristics → Check memory for similar tasks
│   └── Comparison methodology → Check memory for prior comparisons
│
├── Am I making claims that need backing?
│   ├── Performance metrics → memory_load for prior benchmarks
│   ├── Architectural patterns → memory_load for pattern definitions
│   └── Tool capabilities → memory_load for tool documentation
│
└── Should I save this work?
    ├── Novel insight/pattern discovered → memory_save immediately
    ├── Benchmark results → memory_save with metrics
    └── One-off answer → No need to persist
```

---

### Memory Load Strategies by Scenario

#### Strategy 1: Prior Work Retrieval
**Use when:** You've analyzed similar systems before

```python
# Query pattern for prior architecture analyses
query = "architecture investigation [framework-name] components patterns"
threshold = 0.7  # High relevance required
limit = 3        # Top 3 most relevant memories
```

**Example queries:**
- `"Helios framework architecture components tools"` → Prior Helios analysis
- `"agent framework comparison memory pattern gist content"` → Memory design patterns
- `"architecture-investigation skill self-improvement phases"` → Self-improvement history

#### Strategy 2: Pattern Library Lookup
**Use when:** You need established architectural patterns

```python
query = "[pattern-name] pattern agent framework"
threshold = 0.6  # Moderate relevance acceptable
limit = 5        # Broader search for pattern variations
```

**Example queries:**
- `"skills looping model background task scheduler"` → Task scheduling patterns
- `"provider abstraction interface LLM agent"` → Provider design patterns
- `"tool definition pydantic validation schema"` → Tool design patterns

#### Strategy 3: Benchmark Validation
**Use when:** You need to back claims with prior measurements

```python
query = "[metric] benchmark [context]"
threshold = 0.8  # Very high relevance - exact matches preferred
limit = 2        # Top 2 most relevant benchmarks
```

**Example queries:**
- `"token reduction benchmark gist content memory pattern"` → Memory efficiency claims
- `"background task scheduler performance metrics"` → Scheduler benchmarks
- `"provider interface overhead measurement"` → Interface cost analysis

---

### What to Save (Memory Persistence Guidelines)

#### High Priority - Always Save:
1. **Novel architectural patterns discovered** during investigation
2. **Benchmark results with specific metrics** (compression ratios, speedup factors, accuracy retention)
3. **Tool selection heuristics validated** through empirical testing
4. **Framework comparison matrices** with concrete differentiators
5. **Self-improvement phase completions** and lessons learned

#### Medium Priority - Save if Valuable:
1. Research paper key insights (like TurboQuant's two-stage processing pattern)
2. Unusual framework design decisions worth remembering
3. Tool capability discoveries beyond documentation
4. Performance optimization techniques that worked

#### Low Priority - Generally Don't Save:
1. One-off factual lookups easily searchable later
2. Temporary debugging information
3. Conversational context not tied to architectural insights
4. Redundant information already in skills or documentation

---

### Memory Query Construction Best Practices

#### Effective Query Structure:
```
[topic] + [aspect] + [context]
```

**Examples:**
- ❌ `"memory pattern"` → Too vague, low precision
- ✅ `"memory pattern gist content agent framework"` → Specific topic, aspect, context
- ❌ `"Helios tools"` → Missing architectural focus
- ✅ `"Helios skills framework YAML frontmatter architecture"` → Complete query structure

#### Threshold Selection Guide:
| Threshold | Use Case | Example |
 0.8-1.0 | Exact matches needed (benchmarks, specific metrics) | "3-bit quantization zero accuracy loss TurboQuant" |
| 0.6-0.8 | High relevance required (prior work retrieval) | "architecture investigation Helios components" |
| 0.4-0.6 | Exploratory search (pattern discovery, brainstorming) | "agent framework memory patterns" |

---

### Integration with Other Phases

**Complete Decision Flow:**
```
Task arrives
    ↓
[Phase 1] Guardrails check — Am I looping?
    ↓
[Phase 4] Memory check — Have I done this before?
    ├── Yes → Load prior work, build on it
    └── No → Continue to tool selection
        ↓
[Phase 3] Tool selection heuristics — What's the right tool?
        ↓
Execute investigation
        ↓
[Phase 2] Empirical validation — Back claims with data
        ↓
[Phase 4] Memory save — Preserve valuable insights
```

**Memory as Force Multiplier:**
- **Before action:** Load prior work to avoid reinvention
- **During action:** Save discoveries for future use
- **After action:** Preserve key insights and benchmarks

---

### TurboQuant-Inspired Memory Patterns

**Two-Stage Processing Applied to Memory:**
1. **Stage 1 (Primary Retrieval):** Broad query with moderate threshold (0.6) for relevant context
2. **Stage 2 (Refinement):** Narrow query with high threshold (0.8+) for specific metrics/claims

**Zero-Overhead Design Principle:**
- Memory queries should add minimal cognitive overhead
- Use structured query patterns to reduce decision fatigue
- Pre-defined thresholds eliminate per-query calibration

**Theoretical Bounds as Targets:**
- Aim for near-optimal recall (within small constant factor of perfect retrieval)
- Mathematical precision in queries yields better results than heuristic approaches

## Instructions

### Phase 1: Initial Reconnaissance (5-10 minutes)
1. **Read README.md** - Identify purpose, key features, architecture overview
2. **Check directory structure** - Note major components, modules, organization
3. **Identify entry points** - Find main.py, CLI interfaces, initialization code
4. **Note dependencies** - Check requirements.txt or pyproject.toml for architectural hints

### Phase 2: Component Discovery (15-20 minutes)
For each key area, locate and examine:

**Context Management:**
- Search for "context", "memory", "state" in codebase
- Find context schema definitions (look for dataclasses, Pydantic models)
- Identify context storage mechanisms (in-memory, file-based, database)
- Note context size limits and compression strategies

**Tool/Action System:**
- Locate tool registry or action dispatcher
- Examine tool definition format (decorators, classes, schemas)
- Find tool execution pipeline
- Check for tool composition patterns

**Memory/Persistence:**
- Search for memory storage mechanisms
- Identify retrieval patterns (vector search, keyword matching, hybrid)
- Note memory lifecycle management

### Phase 3: Deep Dive Analysis (20-30 minutes)
1. **Trace a complete request/response cycle** - Follow code from entry point through processing to output
2. **Identify key abstractions** - Find core interfaces and base classes
3. **Map data flow** - Track how information moves between components
4. **Note architectural patterns** - Identify design patterns in use (pipeline, registry, factory, etc.)

### Phase 4: Comparison & Synthesis (10-15 minutes)
1. Create comparison matrix for key dimensions:
   - Context schema complexity and structure
   - Tool system flexibility
   - Memory architecture sophistication
   - Extensibility mechanisms
2. Identify unique architectural decisions
3. Note tradeoffs made by each framework

## Output Format
Produce an Architecture Assessment Report with:
- **Executive Summary**: 2-3 paragraph overview of key findings
- **Architecture Diagram**: ASCII or text description of component relationships
- **Key Components Analysis**: Detailed breakdown of major systems
- **Comparison Matrix**: Side-by-side comparison if multiple frameworks analyzed
- **Notable Architectural Decisions**: Key design choices and their implications
- **Recommendations**: Suggestions for adoption, integration, or further investigation

## Example Triggers
- "Investigate the architecture of this agent framework"
- "Compare how these two systems handle context management"
- "Do an architectural assessment of this codebase"
