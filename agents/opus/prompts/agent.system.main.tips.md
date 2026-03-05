## Operational context

### Filesystem
- working directory: /a0/usr/workdir
- knowledge base: /a0/usr/knowledge/
- identity documents: /a0/usr/knowledge/opus/
- extensions: /a0/python/extensions/
- prompts: /a0/prompts/ and /a0/agents/agent0/prompts/

### Extensions
- extensions fire at hooks: before_main_llm_call, monologue_end, message_loop_end
- execution order determined by _XX_ prefix number
- BST (_11) fires before memory enhancement (_20) before context watchdog (_20)
- selective memorizer (_52) fires at monologue_end, before classifier (_55)
- after modifying extension files: clear __pycache__ AND restart container — both caches must be invalidated

### Memory system
- FAISS vector database for persistent memory
- selective memorizer creates memories, classifier (_55) tags them
- knowledge base documents imported on startup — check for chunk-as-conflict issues
- query with created_by: selective_memorizer to find runtime-generated memories

### Known issues
- History class has no __len__ or __getitem__ — use .counter and .output() methods
- concat_messages() ignores its argument — always calls history.output_text() internally
- Python bytecode cache and extension discovery cache are independent — both need clearing on code changes
- Tracebacks show current source file but execute cached bytecode — misleading during hot-reload debugging