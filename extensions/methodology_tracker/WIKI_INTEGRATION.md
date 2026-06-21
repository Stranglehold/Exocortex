# Wiki Integration — program.md Addition

Add this to the operating principles section of program.md (both containers):

```markdown
## Wiki-First Research

Your wiki at workspace/wiki/ is your accumulated institutional knowledge — 300+
pages of research you've written across hundreds of cycles. Before doing any
knowledge-intensive work (writing skills, expanding stubs, composing wiki pages,
producing field reports, answering research questions), search your own wiki first.

The pattern:
1. Read workspace/wiki/index.md to find relevant pages by topic
2. Search filenames in workspace/wiki/research/ for keyword matches
3. Read the top 2-3 matching pages
4. Use that accumulated knowledge to inform your work
5. Cite which wiki pages you drew from

Your wiki is your institutional memory. A 27B model with 300 pages of its own
domain-specific research performs like a much larger model on those domains.
Use what you've already learned before generating from scratch.

When delegating to subagents: include relevant wiki content in the subagent's
instructions. The subagent doesn't have access to your wiki unless you provide it.
Search first, then delegate with context.
```

## Subagent Delegation Integration

When the orchestrating agent delegates a knowledge-intensive task to a subagent,
it should use the wiki_retriever utility to search for relevant pages and include
their content in the subagent's instruction prompt.

The flow becomes:
```
1. Receive knowledge-intensive task
2. Search wiki for relevant pages (wiki_retriever.search_wiki)
3. Read top 2-3 matching pages  
4. Include page summaries in subagent instructions
5. Delegate to subagent WITH wiki context
6. Subagent produces output informed by accumulated knowledge
```

This is the "soft fine-tuning" mechanism: the wiki shapes the model's output
toward domain-specific knowledge without touching a single weight.
