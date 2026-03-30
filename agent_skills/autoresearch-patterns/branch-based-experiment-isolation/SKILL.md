# Branch-Based Experiment Isolation Pattern

## Overview
Use version control branches as state containers for iterative experimentation. Each experiment is isolated, reversible, and traceable through git history.

## Source
Extracted from karpathy/autoresearch experiment loop:
```
LOOP FOREVER:
1. Look at current branch/commit state
2. Tune train.py with experimental idea
3. git commit
4. Run experiment: uv run train.py > run.log 2>&1
5. Read results: grep "^val_bpb:" run.log
6. Record in results.tsv (untracked)
7. If improved → advance branch, keep commit
8. If worse → git reset back to start
```

## Pattern Structure

### Branch as Research State
The branch *is* the research state:
- **Branch name**: `autoresearch/<tag>` (e.g., `autoresearch/mar5`)
- **Commit history**: Sequence of experiments tried
- **HEAD position**: Current best working point
- **Untracked files**: Results log (`results.tsv`) separate from code

### Experiment Loop Mechanics

| Step | Action | Purpose |
|------|--------|----------|
| 1 | Check current branch/commit | Establish baseline state |
| 2 | Modify code with experiment | Apply hypothesis |
| 3 | git commit | Create reversible checkpoint |
| 4 | Run experiment | Test hypothesis |
| 5 | Read results | Measure outcome |
| 6 | Record in tsv (untracked) | Log attempt separately from code |
| 7a | If improved → keep commit | Advance the branch |
| 7b | If worse → git reset | Revert to previous state |

## Application to Agent Zero

### For Iterative Tasks (Debugging, Optimization)

**Setup:**
```bash
# Create work branch for experiment session
git checkout -b experiments/<task-name>-<date>
```

**During iteration:**
1. Make change → commit with descriptive message
2. Test/evaluate the change
3. If successful → keep commit, continue from here
4. If failed → `git reset --hard <previous-commit>` or just don't use that branch path

**Example: Debugging session**
```
$ git checkout -b experiments/debug-auth-issue-20240321
$ # Try fix A
git commit -m "Try fix A: increase token expiry"
# Test → fails, still broken
git reset --hard HEAD~1

$ # Try fix B  
git commit -m "Try fix B: add retry logic"
# Test → works!
# Keep this commit, continue from here
```

### For Subordinate Task Delegation

Frame tasks with experiment isolation:

**Delegation prompt:**
```
Work on branch: experiments/<task>-<date>
For each attempt:
1. Commit before testing (reversible checkpoint)
2. Test your change
3. If it works → keep the commit
4. If not → reset and try different approach
Report back with git log showing attempts made.
```

## Benefits

1. **Reversibility** — Every experiment can be undone cleanly
2. **Traceability** — Git history shows what was tried, in order
3. **Isolation** — Experiments don't pollute main branch until proven
4. **Parallel exploration** — Multiple branches for different hypotheses
5. **Collaboration-friendly** — Others can see experiment history

## Example Applications

### Code Optimization Task
```
Branch: experiments/optimize-query-performance-20240321

Commit 1: "Add database index on user_id" → +15% speedup → KEEP
Commit 2: "Switch to async queries" → crash, OOM → RESET
Commit 3: "Add result caching with 60s TTL" → +40% speedup → KEEP
Commit 4: "Reduce query N+1 with select_related" → +25% more → KEEP

Final: Merged to main with 80% total improvement, full history preserved
```

### Feature Development Task
```
Branch: experiments/add-search-filter-20240321

Commit 1: "Add filter UI component" → works → KEEP
Commit 2: "Connect filter to backend query" → breaks pagination → RESET
Commit 3: "Refactor query builder first" → foundation laid → KEEP  
Commit 4: "Re-add filter connection" → works now → KEEP

Final: Clean history showing correct approach after learning
```

## Integration with Other Patterns

**With Constraint Framing:**
- Fixed: Branch naming convention, commit message format
- Variable: What experiments to try, order of attempts

**With Results Tracking:**
- Record all attempts (including failed ones) in separate log file
- Git history = code changes; results log = outcomes

## Benefits Summary
1. **Reversibility** — Every experiment can be undone cleanly
2. **Traceability** — Git history shows what was tried, in order  
3. **Isolation** — Experiments don't pollute main branch until proven
4. **Parallel exploration** — Multiple branches for different hypotheses
5. **Collaboration-friendly** — Others can see experiment history
