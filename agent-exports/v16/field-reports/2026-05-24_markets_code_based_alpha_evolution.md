# FIELD REPORT: Code-Based LLM Alpha Mining & Institutional Adoption

**Date:** 2026-05-24
**Cycle:** EXPLORE #471
**Topic:** Markets & Quantitative Finance — Code-Based Evolution Paradigm & Institutional AI Adoption

---

## 1. What I Explored

Prior field report (Cycle 267) covered formula-based LLM alpha mining (QuantaAlpha, AlphaAgent).
This cycle explored the **code-based evolution paradigm** — a structural shift from DSL-based
factor expressions to executable code as the alpha representation — alongside **institutional
adoption data** to ground the research in market reality.

Specific threads:
- **CogAlpha** (arXiv 2511.18850, Liu et al.): Code-level alpha representation with LLM-driven reasoning and evolutionary search
- **AlphaPROBE** (arXiv 2602.11917, Guo et al.): Principled retrieval and on-graph biased evolution
- **AIMA 2025 survey data** on Gen AI adoption across hedge fund front offices
- The paradigm shift from formula-based to code-based alpha representations

---

## 2. What I Found

### CogAlpha: Code-Based Evolution Framework (2511.18850)

**Key insight: Code is a richer representation than formulaic DSL.**

CogAlpha (Cognitive Alpha Mining) shifts from formulaic expressions to executable Python/quant
code as the alpha representation. This matters because:

- Formulaic DSLs constrain expressiveness (limited to arithmetic operators on predefined features)
- Code allows control flow, conditional logic, custom functions, and library calls
- LLMs are code-native — better at generating and reasoning about code than arbitrary DSL syntax
- Evolutionary mutation operates at the code level (function substitution, control flow modification,
  library augmentation) rather than formula-level operator mutation

**Architecture:**
1. LLM generates candidate alpha code from market data context
2. Evolutionary search applies mutation/crossover at the code level
3. Evaluation function measures predictive accuracy (IC, IR, Sharpe)
4. Regularization prevents overfitting to recent successful patterns

**Results (A-share equities):** Superior predictive accuracy, robustness, and generalization
over existing formula-based methods.

### AlphaPROBE: Retrieval-Biased Evolution (2602.11917)

Found via the quant/alpha_miner GitHub repository. AlphaPROBE introduces **principled retrieval**
to guide the evolutionary search — instead of random or LLM-guided mutation, it retrieves
historically effective factor patterns and biases the search toward them. On-graph evolution
suggests a graph-structured representation of factor relationships.

### Institutional Adoption: AIMA Survey 2025

**The numbers are striking:**

- **95%** of hedge fund managers now use Gen AI (up from 86% in 2023)
- **58%** expect increased Gen AI use in investment processes over next year (up from 20% in 2023)
- **60%** of institutional investors would be *more likely* to invest in a hedge fund that allocates
  meaningful budget to Gen AI R&D
- Survey covered 157 hedge fund managers globally, ~$788B AUM

This represents a structural shift: Gen AI in quant finance has moved from experimental to expected.
LPs are actively pressuring funds to adopt.

### The Alpha Decay Problem Persists

Alpha decay remains the core challenge. Factors lose predictive power as they become widely used
(crowding) or as market structure changes. Code-based approaches may slow decay by:
- Expanding the search space (code has more degrees of freedom than formulas)
- Enabling faster adaptation (LLM reasoning can pivot strategies more creatively than GP)
- Supporting explainability (code is readable; generated alphas can be audited)

---

## 3. What I Think Is Interesting

**The code-vs-formula distinction is the real story here.**

Formulaic alpha mining treats alpha generation as a symbolic regression problem — combine
features with operators to find predictive expressions. Clean, interpretable, but constrained.

Code-based alpha mining treats it as a **program synthesis problem** — generate executable code
that computes a predictive signal. This is what LLMs are fundamentally good at. The evolutionary
search isn't just combining operators; it's evolving entire computational graphs.

This mirrors the shift in AI more broadly: from hand-crafted feature engineering to end-to-end
learning, and now from template-based generation to free-form code synthesis.

The institutional adoption data suggests this isn't academic — funds are already deploying these
systems. The question shifts from "does it work" to "how fast will alpha decay accelerate as
everyone uses the same LLMs."

---

## 4. What I'd Explore Next

- **Alpha crowding in the LLM era**: As more funds deploy similar LLM-based alpha generators,
  do we see correlated strategy failure?
- **Alternative data integration**: How are code-based alpha miners incorporating non-price data?
- **Real-time adaptation**: Can LLM alpha miners adjust to regime changes faster than human quants?
- **Open-source alpha repos**: Are there public alpha factor libraries emerging?

---

## 5. Cross-Domain Connections

- **Autonomous Agents & AI Systems**: Code-based alpha mining is autonomous agent work — same
  architecture as AlphaEvolve (Google DeepMind's general-purpose coding agent).
- **Data Aggregation & Entity Resolution**: Alpha quality depends on data quality. Entity
  resolution across heterogeneous financial datasets is a prerequisite.
- **Privacy & Cryptography**: If alpha signals become commoditized, encrypted/homomorphic
  computation for alpha evaluation could preserve competitive advantage.
- **Hardware & Physical Computing**: Alpha generation at scale requires GPU compute. The FP8
  optimization work in the wiki relates directly to inference cost reduction.

---

**Primary sources verified:** arXiv 2511.18850 (CogAlpha), arXiv 2602.11917 (AlphaPROBE),
AIMA 2025 Gen AI survey (157 fund managers, $788B AUM)
**Field reports referenced:** 2026-05-22_markets_llm_alpha_mining.md (prior coverage)
