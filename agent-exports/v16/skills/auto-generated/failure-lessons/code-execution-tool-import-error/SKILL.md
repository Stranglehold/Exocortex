---
name: code-execution-tool-import-error
description: "Use before calling code_execution_tool in a context that previously failed with 'import_error'. A required Python package is not installed in the active virtual environment. The correct pip binary is /opt/venv-a0/bin/pip \u2014 bare 'pip' may install into a dif"
triggers: ["code_execution_tool", "code_execution_tool import_error", "import error"]
success_criterion: "Agent installs with /opt/venv-a0/bin/pip and reports a restart is required, instead of bare pip or looping on the import"
confidence: probable
---

# Failure lesson: code_execution_tool — import_error

Captured automatically from a classified tool failure (Cycle-to-Skill Pipeline, Path A). Check this before repeating the operation.

## What happens
A required Python package is not installed in the active virtual environment. The correct pip binary is /opt/venv-a0/bin/pip — bare 'pip' may install into a different environment and have no effect. CRITICAL: even after a successful pip install, the module will NOT be available in the current Python process. Agent Zero must be restarted for new packages to load. Do not loop attempting imports after installing.

Evidence (matched pattern): `ModuleNotFoundError: No module named`

## Avoid
- Do NOT use bare 'pip install' — always use /opt/venv-a0/bin/pip
- Do NOT loop trying the import again after installing — it will fail until restart
- Do NOT attempt more than one install per missing package
- Do NOT try to importlib.reload() or sys.modules tricks — restart is the only fix

## Do instead
- Install the missing package: /opt/venv-a0/bin/pip install <package-name>
- Verify installation: /opt/venv-a0/bin/pip show <package-name>
- After installing, report to the operator that a container restart is required
- Do NOT attempt to use the new package in the same session without restarting
