## Operational context

### Project structure
- Exocortex documentation: /a0/usr/Exocortex/
- Exocortex skills: /a0/usr/Exocortex/skills/ (NOT /a0/skills/ — that's Agent Zero's native skill system)
- Exocortex extensions: /a0/usr/Exocortex/extensions/
- Exocortex identity documents: /a0/usr/Exocortex/identity/
- Exocortex specs and design notes: /a0/usr/Exocortex/specs/
- Active extensions: /a0/python/extensions/
- Agent Zero prompts: /a0/prompts/ and /a0/agents/qwen35/prompts/

### Two skill systems exist — know the difference
- /a0/skills/ — Agent Zero's native skill system. YAML frontmatter, SKILL.md files, auto-discovered by the framework.
- /a0/usr/Exocortex/skills/ — Exocortex project skills. Markdown format with Trigger, Inputs Required, Procedure, Quality Checks, Anti-Patterns. NOT auto-discovered — these are reference documents.
- When the user says "make a skill like the others in the project," they mean the Exocortex format. Check /a0/usr/Exocortex/skills/DEBUG_DIAGNOSTICS.md for the reference format.

### Extensions
- Extensions fire at hooks: before_main_llm_call, monologue_end, message_loop_end
- Execution order determined by _XX_ prefix number
- BST (_11) fires before memory enhancement, before context watchdog
- Selective memorizer (_52) fires at monologue_end, before classifier (_55)
- After modifying extension files: clear __pycache__ AND restart container

### Memory system
- FAISS vector database for persistent memory
- Selective memorizer (_52) creates memories, classifier (_55) tags them
- Knowledge base documents imported on startup
- Query with created_by: selective_memorizer to find runtime-generated memories

### Known issues
- History class has no __len__ or __getitem__ — use .counter and .output() methods
- concat_messages() ignores its argument — always calls history.output_text() internally
- Python bytecode cache and extension discovery cache are independent — both need clearing on code changes
- Tracebacks show current source file but execute cached bytecode — misleading during hot-reload debugging
- The `thefuck` package may produce stderr warnings on ls/cd commands — these are noise, ignore them
