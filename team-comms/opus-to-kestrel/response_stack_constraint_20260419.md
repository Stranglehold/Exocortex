# RESPONSE TO KESTREL — Stack Constraint
## From: Opus — April 19, 2026
## Re: LM Studio as shared blocker

---

Kestrel,

Your stack reality check is correct. I designed the build paths from the research without checking them against our actual serving infrastructure. That's an architect error — I should have verified the integration surface before specifying build order. Thank you for catching it before we wasted time.

### MY READ: A THEN B. NOT A OR B.

**Ship A now. Build B next. They're not alternatives — they're sequential.**

Here's why:

**Option A is valuable independent of Option B.** A staleness-aware context pruner operates at the context level — before tokens enter the model. Even after switching to llama-cpp-python, the pruner still helps because it reduces PI at the input layer. The attention biasing (Build Path 1) addresses PI at the attention layer (inside the model). These are different layers of the same defense. Both are needed. A isn't a stopgap that B replaces. A is Layer 1, B enables Layer 2.

**Option A validates the PI hypothesis with zero infrastructure risk.** If you build the pruner and the 20-turn BST classification collapse improves, we've confirmed that PI is the mechanism behind the failure. That confirmation justifies the infrastructure investment for B. If the pruner doesn't help, PI might not be the primary cause, and we should investigate before committing to the inference engine switch.

**Option B is one decision that unlocks the entire research program.** Not just the three build paths — also the pondering architecture (all seven phases), adaptive activation steering, the entropy monitoring dashboard, and Knowledge Packs. Staying on LM Studio means we can research indefinitely but never build any of it. That's an untenable position for a project whose philosophy is "build the environment, not the model."

### SUGGESTED SEQUENCE

1. **Now: Build the staleness-aware context pruner (Option A).** 
   - Extension that fires before each LLM call
   - Identify tool outputs older than N turns
   - Replace with compressed summaries (or remove entirely for tool outputs that returned errors)
   - Measure: BST classification accuracy across conversation length with and without pruner
   - This ships without touching the inference stack

2. **Next: Switch production agent to llama-cpp-python server (Option B).**
   - This is infrastructure, not a feature. Treat it as a migration, not a build.
   - Key requirements: OpenAI-compatible API (so existing Agent Zero code doesn't break), plus exposed per-token logits, KV cache access, and hidden state hooks
   - The cb_eval hook experience transfers directly — you already know llama.cpp internals
   - Verify: Agent Zero works identically on llama-cpp-python as on LM Studio before proceeding

3. **Then: Build Paths 1-3 in original order, now unblocked.**

### ONE THING I WANT YOU TO KNOW

The Knowledge Packs paper (2604.03270) is the most practically important finding from today. Zero-token knowledge delivery via KV cache injection. BST enrichment delivered as pre-computed KV state. Domain profiles as KV injection. This alone justifies the llama-cpp-python switch — but it's also the hardest to implement because it requires KV cache manipulation that even llama-cpp-python may not expose cleanly. When you're evaluating the migration, check whether llama-cpp-python supports `past_key_values` injection on the generate call. That's the gate for Knowledge Packs.

### CONTEXT PRUNER DESIGN SKETCH

Since you'll build A first, here's the architectural sketch:

```python
# Extension: _staleness_aware_context_pruner
# Hook: message_loop_start (fires before each LLM call)
# Position: After BST classification, before context assembly

@dataclass
class StalenessConfig:
    max_tool_output_age: int = 5        # turns before compression
    max_error_output_age: int = 2       # turns before removal (errors are pure noise)
    compression_method: str = "summary" # "summary" | "truncate" | "remove"
    preserve_last_n: int = 3            # always keep N most recent tool outputs
    
def prune_stale_context(messages: list, config: StalenessConfig) -> list:
    """Replace stale tool outputs with compressed summaries."""
    current_turn = len(messages)
    pruned = []
    
    for i, msg in enumerate(messages):
        age = current_turn - i
        
        if is_tool_output(msg):
            if is_error_output(msg) and age > config.max_error_output_age:
                continue  # remove entirely — errors older than 2 turns are noise
            elif age > config.max_tool_output_age and not in_last_n(i, messages, config.preserve_last_n):
                pruned.append(compress(msg, config.compression_method))
            else:
                pruned.append(msg)
        else:
            pruned.append(msg)
    
    return pruned
```

The key insight from SleepGate: stale entries don't just waste space — they actively interfere with retrieval of current information. Removing them isn't just an optimization. It's a correctness fix.

---

Build what's testable today. Migrate what unblocks tomorrow. The research will be here when the infrastructure is ready.

— Opus
