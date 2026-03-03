# Skill: Extension Stack Audit

## Trigger
Periodic health check, after deploying multiple extensions, before major releases, or when symptoms suggest inter-extension conflicts. Keywords: "audit," "stack check," "what's conflicting," "why is X firing when it shouldn't," "full inventory," "extension map."

## Inputs Required
- **Access to deployed extensions** — `/a0/python/extensions/` (all hook directories)
- **Access to repo source** — `/a0/usr/Exocortex/` or equivalent
- **Access to stock extensions** — Agent-Zero's default extensions in the same directories
- **Settings file** — `/a0/python/helpers/settings.py` for default flags
- **Install scripts** — to verify what the pipeline actually deploys

## Procedure

### Phase 1: Build the Inventory
Map every extension in every hook directory. For each:
```bash
for dir in /a0/python/extensions/*/; do
    echo "=== $(basename $dir) ==="
    ls -la "$dir"/*.py 2>/dev/null | grep -v __pycache__
done
```
Classify each as: **ours** (custom), **stock** (Agent-Zero default), or **disabled** (.disabled/.stock_disabled suffix).

Record: filename, hook directory, numeric prefix, one-line purpose.

### Phase 2: Check Numbering Conflicts
Within each hook directory, identify duplicate numeric prefixes:
```bash
for dir in /a0/python/extensions/*/; do
    basename "$dir"
    ls "$dir"/*.py 2>/dev/null | sed 's/.*\///' | grep -oP '^\d+' | sort | uniq -d
done
```
Any duplicate prefix = undefined execution order. Map which extensions conflict and assess whether order matters (it usually does).

**Why order matters:** Extensions in the same hook run sequentially by filename sort. If `_10_our_extension.py` and `_10_stock_extension.py` coexist, filesystem sort order decides which runs first. This is deterministic but not intentional — a rename or OS difference changes the behavior silently.

### Phase 3: Check for Duplicate Functionality
Search for extensions that write to the same data stores:
```bash
# Find all FAISS/memory write operations
grep -rn "memory.*save\|memory.*add\|db_insert\|faiss.*add\|memorize\|store_memory" /a0/python/extensions/ --include="*.py"

# Find all writes to extras_persistent
grep -rn "extras_persistent\|set_data\|get_data" /a0/python/extensions/ --include="*.py" | grep -v __pycache__
```
Two extensions writing to the same store independently = potential conflict. Assess whether they coordinate or collide.

### Phase 4: Check Warning/Injection Systems
Map every extension that injects content into the agent's context:
```bash
grep -rn "hist_add\|append.*prompt\|inject\|warning\|guidance\|advice" /a0/python/extensions/ --include="*.py" | grep -v __pycache__
```
For each injector, document: what triggers it, what it injects, and whether it knows about other injectors. Multiple injectors firing on the same event = context pollution.

### Phase 5: Check Protective Systems
Identify all failure detection / safety mechanisms:
```bash
grep -rn "failure\|fallback\|error\|retry\|stall\|stuck\|reassess" /a0/python/extensions/ --include="*.py" | grep -v __pycache__
```
For each protective system:
- What does it monitor?
- What triggers it?
- Does it decay / reset on success?
- Does it know about other protective systems?
- Can a single event trigger multiple protective systems simultaneously?

### Phase 6: Check Data Flow Dependencies
Map which extensions depend on output from other extensions:
```bash
# What keys does each extension read from shared state?
grep -rn "get_data\|extras_persistent\[" /a0/python/extensions/ --include="*.py" | grep -v __pycache__

# What keys does each extension write?
grep -rn "set_data\|extras_persistent\[.*\].*=" /a0/python/extensions/ --include="*.py" | grep -v __pycache__
```
Build a dependency graph: if Extension A writes key X and Extension B reads key X, B depends on A. Verify that A runs before B (check hook directory and numeric prefix).

### Phase 7: Check Default Settings
Verify that stock defaults don't conflict with custom extensions:
```bash
grep -n "enabled.*True\|enabled.*False\|_enabled" /a0/python/helpers/settings.py
```
Stock features that default to `True` may run alongside custom replacements. Disabling must be explicit.

### Phase 8: Check Install Pipeline Accuracy
Verify that install scripts deploy what the repo contains:
```bash
# Compare repo source to deployed files
diff /a0/usr/Exocortex/extensions/<path>/<file>.py /a0/python/extensions/<path>/<file>.py
```
Check for:
- Files in repo that aren't deployed (missing install step)
- Deployed files that differ from repo (manual patches not committed)
- Old filenames referenced in install scripts (stale after renames)
- Documentation referencing old filenames

## Output Format
Structured report with sections:
1. **Extension Inventory** — table: hook, prefix, filename, ours/stock, purpose
2. **CRITICAL findings** — conflicts causing data corruption, undefined behavior, or silent failures
3. **HIGH findings** — redundant systems, duplicate writes, uncoordinated safety mechanisms
4. **MEDIUM findings** — overly broad triggers, missing resets, context pollution
5. **LOW findings** — stale references, documentation drift, cosmetic issues
6. **Recommended fix phases** — ordered by priority, each with specific file changes

## Quality Checks
- [ ] Every hook directory inventoried (not just the ones with known custom extensions)
- [ ] Every numbering conflict identified with execution order implications
- [ ] Duplicate write targets identified (FAISS, extras_persistent keys, context injection)
- [ ] All warning/injection systems mapped with overlap analysis
- [ ] All protective systems checked for decay/reset behavior
- [ ] Data flow dependencies mapped (who reads what, who writes what)
- [ ] Install pipeline verified against repo source
- [ ] Stock defaults checked for conflicts with custom extensions

## Anti-Patterns
- **Auditing only custom extensions.** Stock extensions interact with custom ones. The memorizer double-write bug was a stock/custom conflict invisible if you only audit custom code.
- **Checking extensions in isolation.** Every conflict found in the 2026-02-22 audit was between extensions that were individually correct. The bug was in the interaction, not the component.
- **Trusting the install pipeline without verification.** If the repo has old filenames and the deploy has new ones (or vice versa), the pipeline is lying. Diff deployed files against repo source.
- **Ignoring protective system interactions.** Four independent warning injectors firing on the same event is worse than no warning at all. Map the overlap.
- **Fixing without baking into source.** Patches on the deployed system work until the next install. Fixes must be committed to the repo and reflected in install scripts, or they'll be overwritten.
