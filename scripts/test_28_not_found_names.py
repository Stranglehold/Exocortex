"""Controls for ruling 5: _28_output_compressor keeps every tool name in a "tool not found" response.

Drives the candidate's real execute() with a fake Response, the way A0 calls tool_execute_after
(response=..., tool_name=...). A0's modules are stubbed so this runs on the host.
"""
import asyncio
import importlib.util
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))

# ── stubs for the two A0 imports the extension makes ──
agent_mod = types.ModuleType("agent")
class LoopData:  # noqa: E302
    pass
agent_mod.LoopData = LoopData
helpers_mod = types.ModuleType("helpers")
ext_mod = types.ModuleType("helpers.extension")
class Extension:  # noqa: E302
    def __init__(self, agent=None, **kw):
        self.agent = agent
ext_mod.Extension = Extension
sys.modules.update({"agent": agent_mod, "helpers": helpers_mod, "helpers.extension": ext_mod})

spec = importlib.util.spec_from_file_location("c28", os.path.join(HERE, "..", "plugins", "_exocortex", "extensions", "python", "tool_execute_after", "_28_output_compressor.py"))
c28 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c28)
c28._load_cfg = lambda agent: {}          # defaults: enabled, threshold 800, 30/30


class FakeLog:
    def __init__(self): self.items = []
    def log(self, **kw): self.items.append(kw)


class FakeAgent:
    def __init__(self):
        self.context = types.SimpleNamespace(log=FakeLog())


class Resp:
    def __init__(self, message): self.message = message


def run(tool_name, text):
    r = Resp(text)
    ext = c28.ToolOutputCompressor(agent=FakeAgent())
    asyncio.run(ext.execute(tool_name=tool_name, response=r))
    return r.message, ext.agent.context.log.items


DESC = "\n".join(f"description line {i} for this tool, with usage notes and an example" for i in range(18))
LOCAL = ["a2a_chat", "autoresearch", "call_subordinate", "code_execution_tool", "document_query",
         "notify_user", "response", "scheduler",
         "search_engine", "skills_tool", "swarmfish_predict", "text_editor", "wait"]
# Production shape of the _memory plugin's prompt (plugins/_memory/prompts/agent.system.tool.memory.md):
# one "## memory tools" section declaring several tools as "- `name`: args ..." bullets, no ### headings.
MEMORY_BLOCK = ("## memory tools\nuse memory tools to store and recall durable information\n"
                "- `memory_load`: args `query`, optional `threshold`, `limit`, `filter`; search memories\n"
                "- `memory_save`: args `text`, optional `area` and metadata; store durable information\n"
                "- `memory_delete`: args `ids`; delete memories by id\n"
                "- `memory_forget`: args `query`, optional `threshold`, `filter`; remove matching memories\n"
                "rules:\n- use `memory_save` for stable current facts, not short-lived test markers\n"
                "- `decoy_note`: a note about memory hygiene, not a tool declaration")
DECLARED = ["memory_load", "memory_save", "memory_delete", "memory_forget"]
# Production shape of _a0_connector's remote tools: a level-1 title, then "## Arguments".
REMOTE_BLOCK = ("# code_execution_remote tool\nrun code on the connected CLI host\n\n## Arguments\n"
                "- `runtime`: one of `terminal`, `python`\n- `session`: integer session id\n\n"
                "# Usage Notes For Remote Hosts\nplain prose title, not a tool")


def not_found_text(name, template="stock"):
    parts = []
    for t in LOCAL:
        header = f"### {t}:" if t == "swarmfish_predict" else f"### {t}"
        parts.append(f"{header}\n{DESC}\n~~~json\n{{\n  \"tool_name\": \"{t}\",\n  \"tool_args\": {{}}\n}}\n~~~")
    local = ("## available tools\nuse ONLY the tools listed below. match names exactly.\n" + "\n\n".join(parts)
             + "\n\n" + MEMORY_BLOCK + "\n\n" + REMOTE_BLOCK)
    vision = "## multimodal vision tools\n\n### vision_load\n" + DESC
    mcp = ('## "Remote (MCP Server) Agent Tools" available:\n\nServer descriptions are context, not callable.\n\n'
           "### MCP server `exocortex_memory` (group only; not a tool)\nContext only: project memory\n\n"
           + "\n\n".join(f"#### MCP tool `exocortex_memory.{t}`\nAllowed operation (exhaustive): x\n\n"
                         f"##### Input schema for tool_args:\n{{\"query\": \"string\"}}\n\n##### Usage:\n{{}}"
                         for t in ("search_memory", "search_all", "search_library", "list_collections"))
           + "\n\n### MCP server `arxiv` (group only; not a tool)\nContext only: papers\n\n"
           "#### MCP tool `arxiv.search_papers`\nAllowed operation (exhaustive): y\n\n##### Usage:\n{}")
    tools = local + "\n\n" + vision + "\n\n" + mcp
    if template == "stock":
        return f"Tool {name} not found. Available tools: \\n{tools}"
    return (f'Tool "{name}" does not exist. You must use one of the available tools listed below.\n\n'
            f"Available tools:\n{tools}\n\nSelect a tool from this list and output a valid JSON response.")


passed = failed = 0
def check(label, cond):  # noqa: E302
    global passed, failed
    print(("  PASS  " if cond else "  FAIL  ") + label)
    passed += bool(cond)
    failed += (not cond)


print("1. positive control: #751's shape (stock v2.12 template)")
text = not_found_text("exocortex_memory.memory_save")
out, logs = run("exocortex_memory.memory_save", text)
if "--show" in sys.argv:
    print("----- what she would see -----\n" + out + "\n------------------------------")
check(f"compressed ({len(text)} -> {len(out)} chars)", len(out) < len(text) // 10)
for n in LOCAL + ["vision_load", "exocortex_memory.search_memory", "exocortex_memory.search_all",
                  "exocortex_memory.search_library", "exocortex_memory.list_collections", "arxiv.search_papers"]:
    if n not in out:
        check(f"name kept: {n}", False)
check("every one of the 22 tool names kept", all(n in out for n in LOCAL + DECLARED + ["vision_load", "arxiv.search_papers"]))
check("declared bullets kept, under their own section", "- memory tools: memory_load, memory_save, memory_delete, memory_forget" in out)
check("a backticked bullet WITHOUT 'args' is not taken as a tool (decoy_note)", "decoy_note" not in out)
check("a level-1 '# <name> tool' title is kept (code_execution_remote)", "code_execution_remote" in out)
check("'## Arguments' and a multi-word '# ...' title are not tools",
      "Arguments" not in out and "Usage" not in out and "runtime" not in out)
check("memory_save is in the kept list (the one #751 lost)", "memory_save," in out or out.rstrip().endswith("memory_save"))
check("server shown as a group, not a tool", "MCP server `exocortex_memory` (a group, not a tool)" in out)
names_lines = [l for l in out.splitlines()[2:]]
check("bare server name never listed as a tool", not any(
    (", exocortex_memory," in l or l.endswith(": exocortex_memory") or ": exocortex_memory," in l) for l in names_lines))
check("'##### Input schema' never taken as a tool", "Input" not in out)
check("first line kept as the not-found statement", out.splitlines()[0] == "Tool exocortex_memory.memory_save not found.")
check("log says the names were kept", any("every tool name kept" in str(i.get("content", "")) for i in logs))

print("2. the older template shape ('does not exist') is recognised too")
out2, _ = run("web_search", not_found_text("web_search", template="fw"))
check("detected and names kept", "search_engine" in out2 and "lines omitted" not in out2)

print("3. negative control: an ordinary large output still gets head + tail")
big = "\n".join(f"build step {i}: compiling module_{i}.py ... ok" for i in range(2000))
out3, _ = run("code_execution_tool", big)
check("head + tail marker present", "lines omitted" in out3)

print("4. a not-found line for a DIFFERENT tool name is not this shape")
out4, _ = run("code_execution_tool", "Tool foo not found. Available tools: \\n" + big)
check("falls back to head + tail", "lines omitted" in out4)

print("5. not-found shape with no recognisable headers: falls back, never empty")
flat = "Tool zzz not found. Available tools: \\n" + "\n".join(f"plain line {i}" for i in range(2000))
out5, _ = run("zzz", flat)
check("head + tail marker present", "lines omitted" in out5)

print("6. below the threshold nothing changes")
small = "Tool tiny not found. Available tools: \\n### a\n### b"
out6, _ = run("tiny", small)
check("unchanged", out6 == small)

print(f"\nRESULT: {passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
