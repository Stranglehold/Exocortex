# GEPA Phase 2 Implementation Brief

**Purpose:** Pre-resolved architectural decisions for the agent to use when implementing
GEPA Phase 2. Eliminates the need for the agent to rediscover these through trial and error.

**Target output:** Four new files in `/a0/usr/skills/gepa/`:
- `phase2_bst_scorer_utils.py` — portable BST scoring (no A0 dependencies)
- `phase2_reflection.py` — ReflectionEngine class
- `phase2_mutation.py` — MutationOperator class  
- `phase2_scorer.py` — BST_Evaluator (extends Phase 1 EvaluationEngine)
- `phase2_test.py` — integration test

---

## Critical Decision: BST Import Problem

**The problem:** The BST extension (`_11_belief_state_tracker.py`) contains the scoring
function we need, but it cannot be imported directly. Lines 31-32:
```python
from agent import LoopData
from helpers.extension import Extension
```
These imports require the full Agent Zero runtime. Any `import _11_belief_state_tracker`
will fail with `ModuleNotFoundError: No module named 'agent'`.

**The solution:** Extract the portable parts into a standalone file.

The following sections of the BST are pure Python (zero A0 imports):
- `DOMAIN_CONFIGS` dict (line 103-400+) — the domain signal patterns
- `DOMAIN_PRIORITY` dict (line ~76-92) — tiebreak priorities
- `_COMPILED_DOMAIN_CONFIGS` compilation block (line ~430-433) — pre-compiles regex
- `_score_all_domains()` function (line 472-490) — the scorer
- `_extract_compound()` function (line ~443-464) — primary/secondary extraction

**Create `phase2_bst_scorer_utils.py`** by copying exactly these sections from the BST file.
No modification needed — they're already self-contained. The scorer imports from this file,
not from the BST extension.

```python
# phase2_bst_scorer_utils.py
# Extracted from _11_belief_state_tracker.py — pure Python, no A0 dependencies
import re

DOMAIN_PRIORITY = { ... }  # copy verbatim
DOMAIN_CONFIGS = { ... }   # copy verbatim

_COMPILED_DOMAIN_CONFIGS = {}
for _dname, _dcfg in DOMAIN_CONFIGS.items():
    _COMPILED_DOMAIN_CONFIGS[_dname] = {
        **_dcfg,
        "_signals_rx": [re.compile(s, re.IGNORECASE) for s in _dcfg["signals"]],
    }

def _score_all_domains(message: str) -> list:
    ...  # copy verbatim

def _extract_compound(scores: list) -> tuple:
    ...  # copy verbatim
```

This approach is safe: we're using the BST as a READ source, not an import target.

---

## Module Interface Contracts

### ReflectionEngine (phase2_reflection.py)

```python
@dataclass
class ClassificationTrace:
    input_message: str
    expected_domain: str
    actual_domain: str          # what BST v3.1 returned
    signals_fired: list[str]    # which regex patterns matched
    signals_missed: list[str]   # patterns that SHOULD have fired (derived)

@dataclass
class Reflection:
    trace: ClassificationTrace
    critique: str               # natural language: what went wrong and why
    root_cause: str             # specific: which signal was missing or overfiring
    mutation_proposals: list[dict]  # [{type, domain, pattern, rationale}]

class ReflectionEngine:
    def reflect(self, trace: ClassificationTrace) -> Reflection: ...
    def batch_reflect(self, traces: list[ClassificationTrace]) -> list[Reflection]: ...
```

The `critique` should be specific: not "investigation fired incorrectly" but
"investigation fired because `\bverif` matched 'verify' — this is a debugging context,
not an OSINT investigation."

The `root_cause` should identify the exact signal: "Signal `\bverif` in investigation
is too broad — fires on 'verify deployment' which is system_admin, not investigation."

The `mutation_proposals` should be concrete:
```python
{"type": "SIGNAL_REMOVE", "domain": "investigation", "pattern": r"\bverif", 
 "rationale": "Fires on debugging/deployment verification, not just OSINT"}
{"type": "SIGNAL_ADD", "domain": "coding", "pattern": r"\bbuild\b.{0,40}\b(?:project|tool|script)\b",
 "rationale": "Captures 'build a two-file project' pattern missed by v3.1"}
```

### MutationOperator (phase2_mutation.py)

```python
class MutationOperator:
    def generate_variants(self, reflection: Reflection, n_variants: int = 3) -> list[dict]:
        """
        Takes a reflection and generates N modified DOMAIN_CONFIGS dicts.
        Each variant applies one or more mutation_proposals from the reflection.
        Returns list of {"domain_configs": {...}, "mutations_applied": [...], "description": str}
        """
    
    def apply_mutation(self, domain_configs: dict, proposal: dict) -> dict:
        """Apply a single mutation proposal to a domain_configs copy. Returns modified copy."""
```

Mutation types:
- `SIGNAL_ADD` — append a regex to domain's signal list
- `SIGNAL_REMOVE` — remove a regex from domain's signal list
- `PRIORITY_ADJUST` — change domain's priority value in DOMAIN_PRIORITY
- `SIGNAL_REPLACE` — replace a broad signal with a narrower one

Each variant should be independently scoreable — don't apply conflicting mutations
to the same variant.

### BST_Evaluator (phase2_scorer.py)

```python
from phase2_bst_scorer_utils import _score_all_domains, _extract_compound, DOMAIN_PRIORITY
from gepa import EvaluationEngine

class BST_Evaluator(EvaluationEngine):
    def evaluate(self, domain_configs_variant: dict, inputs: list[dict]) -> dict:
        """
        Scores a DOMAIN_CONFIGS variant against the training set.
        inputs: [{"input": str, "expected": str}, ...]
        Returns: {
            "accuracy": float,              # correct / total
            "correct": int,
            "total": int,
            "per_domain_precision": dict,   # domain -> precision score
            "false_positive_domains": list, # domains that over-fired
            "missed_domains": list,         # domains that under-fired
            "per_example": list             # per-input breakdown
        }
        """
```

The evaluator must compile new regex from the variant's signal lists on each call —
don't reuse compiled patterns from the utils file.

---

## Training Data

```python
TRAINING_SET = [
    # v3.1 misclassifications — what Phase 2 must learn from
    {"input": "What tools do you have access to right now? List all of them.",
     "expected": "conversation", "v31_actual": "investigation"},
    
    {"input": "Write a Python script that defines 10 Iran war headlines, scores sentiment "
              "using keyword matching, identifies top 3 negative and positive, outputs JSON.",
     "expected": "coding", "v31_actual": "investigation"},
    
    {"input": "Build a two-file Python project. File 1: threat_assess.py with 5 threat "
              "levels and score_text function. File 2: run_threats.py.",
     "expected": "coding", "v31_actual": "conversation"},
    
    {"input": "Find 3 current facts about China position on Iran blockade from real sources. "
              "Write a Python Caesar cipher function shift 13. Write results to combined_output.txt",
     "expected": "coding", "v31_actual": "investigation"},
    
    {"input": "look into the logs to verify the extension loaded correctly",
     "expected": "conversation", "v31_actual": "investigation"},
    
    {"input": "Build a new OSS tool that tracks narrative drift across topics.",
     "expected": "planning", "v31_actual": "conversation"},
    
    {"input": "What is the current S&P 500 price and latest AAPL earnings? Macro analysis needed.",
     "expected": "financial", "v31_actual": "conversation"},
    
    # v3.2 correct cases — variants that improve v3.1 must not break these
    {"input": "OSINT investigation: who owns and controls this entity? Due diligence on credit risk.",
     "expected": "investigation", "v31_actual": "investigation"},
    
    {"input": "Before we start let me figure out how to approach this. Break it down step by step.",
     "expected": "planning", "v31_actual": "planning"},
    
    {"input": "debug this error: AttributeError on line 42",
     "expected": "bugfix", "v31_actual": "bugfix"},
]
```

The last three are **control cases** — correct in both v3.1 and v3.2. Any mutation that
breaks them should be penalized in scoring.

---

## Success Criteria

**Minimum pass:** All four modules import cleanly and `phase2_test.py` runs without errors.

**Full pass:** At least one mutation candidate scores higher accuracy than v3.1 baseline
(7/10 correct = 70%), AND at least one proposed mutation resembles either:
- Adding `\bbuild\b` (or similar) to coding signals
- Removing `\bverif` (or narrowing) from investigation signals

**Stretch goal:** Top candidate scores ≥ 9/10 (90%) on the training set.

---

## What NOT to Do

- Do not try to `import _11_belief_state_tracker` directly — use `phase2_bst_scorer_utils.py`
- Do not modify `gepa.py` (Phase 1) — extend it
- Do not reimplement what Phase 1 already has (Trajectory, PromptVariant, etc.)
- Do not make the reflection module call an LLM — it should be deterministic rule-based
  analysis of which signals fired vs which should have fired
- Do not generate regex patterns that use lookahead/lookbehind unless you verify they
  work with Python's `re` module — stick to simple patterns
