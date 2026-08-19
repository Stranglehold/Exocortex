---
name: tool-design
description: >-
  Design, audit, and optimize agent tool interfaces. Covers tool taxonomy, schema design,
  naming conventions, Agent Zero integration, MCP tool contracts, consolidation strategies,
  testing protocols, and anti-pattern detection. Use when creating new tools, refactoring
  existing tool surfaces, or designing MCP-compatible tool APIs.
triggers:
  - "design agent tools"
  - "create tool descriptions"
  - "reduce tool complexity"
  - "implement MCP tools"
  - "tool consolidation"
  - "tool naming conventions"
  - "agent-tool interfaces"
  - "tool schema design"
  - "tool anti-patterns"
version: 3.0.0
author: Exocortex
tags:
  - tool-design
  - agent-architecture
  - mcp
  - schema-design
  - api-contracts
---

# Tool Design for AI Agents

Production-grade tool design for autonomous agent systems. This skill covers the complete
lifecycle from initial tool specification through integration, testing, and optimization.

## 1. Tool Design Fundamentals

A well-designed agent tool is a single, predictable operation with a clearly defined contract.
Agents reason about tools through their descriptions and schemas alone. Ambiguity in tool
design propagates as hallucination in agent behavior.

### Core Properties

| Property | Definition | Why It Matters |
|----------|-----------|----------------|
| **Atomicity** | One tool performs one logical operation | Agents compose tools sequentially; multi-operation tools create branching ambiguity |
| **Idempotency** | Repeated calls with same args produce same result | Enables retry logic, reduces side-effect anxiety in agent planning |
| **Deterministic I/O** | Same input always produces same output shape | Agents parse tool responses programmatically; schema drift breaks downstream logic |
| **Self-Documenting** | Name, args, and description fully specify behavior | Agent has no runtime introspection beyond the tool prompt |
| **Fail-Fast** | Errors surface immediately with actionable messages | Agents cannot recover from silent failures; they compound errors |
| **Observable** | Tool execution produces structured logs | Debugging agent behavior requires traceability through tool invocations |

### The Atomicity Principle

Each tool should answer a single question or perform a single action:

~~~python
# BAD: Multi-operation tool
def manage_user(action, user_id, name, email, role):
    """Create, update, or delete a user."""
    ...

# GOOD: Atomic tools
def create_user(user_id: str, name: str, email: str) -> User:
    """Create a new user. Fails if user_id already exists."""
    ...

def update_user(user_id: str, **changes) -> User:
    """Update specific fields of an existing user."""
    ...

def delete_user(user_id: str) -> bool:
    """Delete a user. Returns True if deleted, False if not found."""
    ...
~~~

### Idempotency Patterns

| Operation | Idempotent? | Pattern |
|-----------|-------------|---------|
| Read/Query | Yes | Inherently idempotent |
| Create | No | Use "create-if-not-exists" or return existing resource |
| Update | Yes | Set-based updates are idempotent |
| Delete | Yes | Delete non-existent resource returns success |
| Append | No | Use idempotency keys or deduplication |

## 2. Tool Taxonomy

Classify tools by their effect on system state. Classification drives validation strategy,
error handling, and agent trust models.

### Category Definitions

| Category | Effect | Examples | Validation Level |
|----------|--------|----------|------------------|
| **Read-only** | No state change | `query`, `search`, `list`, `get`, `describe` | Input validation only |
| **Write** | Creates/modifies state | `create`, `update`, `delete`, `patch`, `save` | Input validation + pre-condition checks |
| **Execute** | Runs computation/process | `run`, `process`, `transform`, `analyze`, `build` | Input validation + resource checks |
| **Communicate** | External interaction | `chat`, `notify`, `broadcast`, `send`, `call` | Input validation + recipient validation |

### Read-Only Tools

Read-only tools are the safest and most frequently called. Design them for low latency and
high throughput.

~~~json
{
  "tool_name": "search_engine",
  "tool_args": {
    "query": "keyword-based search string",
    "limit": 10,
    "source": "web"
  }
}
~~~

**Design rules:**
- Never produce side effects (no logging to external systems, no caching writes)
- Return empty results, not errors, for zero-match queries
- Support pagination via `offset`/`limit` or cursor-based continuation
- Cache aggressively; read-only tools are called repeatedly during agent reasoning

### Write Tools

Write tools mutate state. They require explicit confirmation patterns and rollback awareness.

~~~json
{
  "tool_name": "text_editor",
  "tool_args": {
    "action": "write",
    "path": "/path/to/file.md",
    "content": "file contents"
  }
}
~~~

**Design rules:**
- Return the full resulting state, not just a success flag
- Include `dry_run` parameter for destructive operations
- Validate all pre-conditions before mutation (file exists, permissions, dependencies)
- Return structured diff for update operations when feasible

### Execute Tools

Execute tools perform computation. They may be long-running and require polling patterns.

~~~json
{
  "tool_name": "code_execution_tool",
  "tool_args": {
    "runtime": "python",
    "code": "print("hello")",
    "session": 0
  }
}
~~~

**Design rules:**
- Support session-based state for multi-step workflows
- Return `runtime: "output"` polling mechanism for long operations
- Include timeout and resource limit parameters
- Capture stdout, stderr, and exit code separately

### Communicate Tools

Communicate tools interact with external systems or users.

~~~json
{
  "tool_name": "a2a_chat",
  "tool_args": {
    "agent_url": "http://agent.example.com/a2a",
    "message": "What is the status?"
  }
}
~~~

**Design rules:**
- Include connection timeout and retry parameters
- Return structured response with status, content, and metadata
- Support message history/context preservation via session identifiers
- Validate recipient availability before sending

## 3. Schema Design

Tool schemas are the contract between agent and tool. The agent sees only the schema and
description. Everything needed to call the tool correctly must be in the schema.

### Input Schema Best Practices

| Principle | Rule | Example |
|-----------|------|---------|
| **Required vs Optional** | Mark only truly required args as required | `path` required, `line_from` optional |
| **Type Constraints** | Use specific types, not generic strings | `integer` not `string` for counts |
| **Defaults** | Provide sensible defaults for optional args | `limit: 50`, `offset: 0` |
| **Enums** | Use enums for fixed sets of values | `action: ["read", "write", "patch"]` |
| **Ranges** | Specify min/max for numeric args | `limit: {"min": 1, "max": 200}` |
| **Descriptions** | Every arg needs a description explaining purpose and constraints | |

### Schema Example

~~~json
{
  "type": "object",
  "properties": {
    "action": {
      "type": "string",
      "enum": ["read", "write", "patch"],
      "description": "Operation to perform on the file"
    },
    "path": {
      "type": "string",
      "minLength": 1,
      "description": "Absolute or relative file path"
    },
    "line_from": {
      "type": "integer",
      "minimum": 1,
      "description": "Starting line number (1-based, inclusive). Default: 1"
    },
    "line_to": {
      "type": "integer",
      "minimum": 1,
      "description": "Ending line number (1-based, inclusive). Omit for no upper bound"
    },
    "content": {
      "type": "string",
      "description": "File content for write/patch operations"
    }
  },
  "required": ["action", "path"]
}
~~~

### Output Schema Design

Tool responses must be structured and parseable. Avoid free-text responses from tools.

| Response Type | Format | Example |
|---------------|--------|---------|
| **Success** | Structured data matching expected schema | `{"status": "ok", "data": {...}}` |
| **Empty Result** | Valid schema with empty collections | `{"results": [], "total": 0}` |
| **Error** | Structured error with code, message, details | `{"error": {"code": "NOT_FOUND", "message": "..."}}` |
| **Partial** | Results with truncation indicator | `{"results": [...], "truncated": true, "total": 150}` |

### Error Format Standard

~~~json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Path must be an absolute path",
    "details": {
      "field": "path",
      "value": "relative/path.txt",
      "constraint": "must_start_with_slash"
    }
  }
}
~~~

**Error code taxonomy:**

| Code | Meaning | Retry? |
|------|---------|--------|
| `VALIDATION_ERROR` | Input failed schema validation | Fix input |
| `NOT_FOUND` | Target resource does not exist | Check target |
| `PERMISSION_DENIED` | Insufficient access rights | Escalate |
| `RATE_LIMITED` | Too many requests | Wait and retry |
| `INTERNAL_ERROR` | Unexpected server error | Retry with backoff |
| `TIMEOUT` | Operation exceeded time limit | Retry with longer timeout |
| `CONFLICT` | State conflict (e.g., file modified) | Re-read and retry |

## 4. Tool Naming & Organization

Tool names are the primary discovery mechanism. Agents search tool names before reading
descriptions. Naming consistency reduces cognitive load and prevents tool confusion.

### Naming Conventions

| Rule | Pattern | Examples |
|------|---------|----------|
| **Verb-Noun** | `action_target` | `search_engine`, `read_file`, `create_user` |
| **Lowercase with underscores** | `snake_case` | `code_execution_tool`, `memory_load` |
| **Domain prefix** | `domain_action` | `gitnexus.query`, `camofox_browse` |
| **No abbreviations** | Spell out fully | `search_engine` not `search_eng` |
| **Consistent verbs** | Use same verb for same action | `create` not `add/make/new` |

### Verb Taxonomy

| Verb | Meaning | Category |
|------|---------|----------|
| `get` | Retrieve single resource | Read |
| `list` | Retrieve collection | Read |
| `search` | Query with filters | Read |
| `query` | Execute structured query | Read |
| `create` | Add new resource | Write |
| `update` | Modify existing resource | Write |
| `delete` | Remove resource | Write |
| `patch` | Partial update | Write |
| `run` | Execute process | Execute |
| `execute` | Run command/script | Execute |
| `analyze` | Process and return insights | Execute |
| `send` | Transmit message | Communicate |
| `chat` | Interactive conversation | Communicate |

### Tool Grouping

Group related tools under a common prefix or namespace:

| Group | Tools |
|-------|-------|
| `memory_*` | `memory_load`, `memory_save`, `memory_delete`, `memory_forget` |
| `gitnexus.*` | `gitnexus.query`, `gitnexus.context`, `gitnexus.impact` |
| `camofox_*` | `camofox_browse`, `camofox_session`, `camofox_media` |
| `swarmfish_*` | `swarmfish_predict`, `swarmfish_session`, `swarmfish_calibration` |

### Versioning Strategy

| Change Type | Version Bump | Backward Compatible? |
|-------------|--------------|---------------------|
| New optional arg | Patch (1.0.x) | Yes |
| New tool added | Patch (1.0.x) | Yes |
| Arg renamed | Major (x.0.0) | No |
| Response shape changed | Major (x.0.0) | No |
| Behavior changed | Minor (x.y.0) | Depends |

## 5. Agent Zero Integration

Agent Zero tools follow a specific registration and execution pattern. Tools are declared
in the system prompt and invoked through JSON tool calls.

### Tool Registration

Tools are registered in the Agent Zero system prompt under the `## available tools` section.
Each tool entry includes:

1. **Tool name** (exact identifier used in `tool_name` field)
2. **Description** (what the tool does, when to use it)
3. **Arguments schema** (parameter names, types, defaults, descriptions)
4. **Usage example** (JSON call demonstrating correct invocation)

### Tool Prompt Template

~~~markdown
### tool_name
Brief description of what the tool does and when to use it.

**Parameters:**

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `param1` | Yes | — | Description of parameter |
| `param2` | No | `default` | Description with constraints |

**Example:**
~~~json
{
  "tool_name": "tool_name",
  "tool_args": {
    "param1": "value",
    "param2": "optional"
  }
}
~~~
~~~

### Tool Handler Implementation

Tool handlers receive `tool_args` as a dictionary and return structured results.

~~~python
def handle_tool_call(tool_name: str, tool_args: dict) -> dict:
    """Execute a tool call and return structured result."""
    # 1. Validate args against schema
    validate(tool_name, tool_args)

    # 2. Execute tool logic
    result = execute(tool_name, tool_args)

    # 3. Log invocation
    log_tool_call(tool_name, tool_args, result)

    # 4. Return structured response
    return result
~~~

### Error Handling in Agent Zero

Tool errors must be returned as structured text that the agent can parse:

~~~python
# Tool handler error response
return {
    "error": True,
    "code": "VALIDATION_ERROR",
    "message": "Required argument 'path' is missing",
    "details": {"missing_fields": ["path"]}
}
~~~

### Logging Invocations

Every tool call should be logged for debugging and analysis:

~~~python
{
    "timestamp": "2026-06-21T01:00:00Z",
    "tool_name": "search_engine",
    "tool_args": {"query": "AI trends 2026"},
    "result_summary": "12 results returned",
    "duration_ms": 245,
    "status": "success"
}
~~~

## 6. MCP Tool Design

Model Context Protocol (MCP) tools follow a JSON-RPC contract with specific capability
declaration and session management requirements.

### MCP JSON-RPC Contract

~~~json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "search_engine",
    "arguments": {
      "query": "AI trends 2026"
    }
  }
}
~~~

### Capability Declaration

MCP servers declare capabilities during initialization:

~~~json
{
  "capabilities": {
    "tools": {
      "listChanged": true
    },
    "resources": {
      "subscribe": true,
      "listChanged": true
    }
  }
}
~~~

### MCP Error Codes

| Code | Name | Meaning |
|------|------|---------|
| `-32700` | Parse Error | Invalid JSON |
| `-32600` | Invalid Request | Malformed request |
| `-32601` | Method Not Found | Unknown tool/method |
| `-32602` | Invalid Params | Argument validation failed |
| `-32603` | Internal Error | Server-side error |
| `-32000` to `-32099` | Server Error | Application-specific errors |

### Session Management

MCP sessions maintain state between calls:

| Aspect | Strategy |
|--------|----------|
| **Session ID** | Generated on connection, included in all messages |
| **State** | Server maintains per-session state (context, history) |
| **Lifecycle** | Open → Active → Close; idle timeout configurable |
| **Reconnection** | Client can resume session or start fresh |

### MCP Tool Definition Format

~~~json
{
  "name": "search_engine",
  "description": "Find live news, prices, and real-time web data",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Keyword-based search query"
      }
    },
    "required": ["query"]
  }
}
~~~

## 7. Tool Consolidation & Reduction

Tool surface area directly impacts agent decision quality. Too many tools create choice
paralysis; too few create capability gaps.

### When to Merge Tools

| Signal | Action |
|--------|--------|
| Two tools share >70% of arguments | Merge with `action` discriminator |
| Tools are always called in sequence | Combine into single workflow tool |
| Tools differ only by target system | Abstract target behind parameter |
| Tools have identical output schemas | Merge with unified input |

### When to Split Tools

| Signal | Action |
|--------|--------|
| Tool has >8 parameters | Split by functional concern |
| Tool performs unrelated operations | Split into atomic tools |
| Tool has conditional logic branches | Split into specialized tools |
| Tool description exceeds 3 sentences | Likely doing too much |

### Consolidation Example

~~~python
# BEFORE: Three separate tools
def search_web(query: str) -> Results: ...
def search_academic(query: str) -> Results: ...
def search_news(query: str) -> Results: ...

# AFTER: Unified tool with source parameter
def search(query: str, source: str = "web") -> Results:
    """Search across multiple sources. Source: web, academic, news, all."""
    ...
~~~

### Reduction Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Tool count** | <20 active tools | Count registered tools |
| **Avg args per tool** | <5 | Schema analysis |
| **Tool overlap** | <10% | Argument similarity matrix |
| **Unused tools** | 0% | Invocation frequency analysis |
| **Description clarity** | >90% agent comprehension | Agent error rate on tool selection |

## 8. Testing & Validation

Tool testing validates the contract between agent and tool. Tests verify schema compliance,
behavioral correctness, and error handling.

### Unit Testing Tools

~~~python
import pytest

def test_search_engine_valid_query():
    result = search_engine({"query": "AI trends"})
    assert "results" in result
    assert isinstance(result["results"], list)
    assert len(result["results"]) <= 10

def test_search_engine_empty_query():
    result = search_engine({"query": ""})
    assert result["results"] == []
    assert result["total"] == 0

def test_search_engine_missing_query():
    with pytest.raises(ValidationError):
        search_engine({})
~~~

### Integration Testing

~~~python
def test_tool_workflow():
    """Test multi-tool workflow: search → read → analyze."""
    # Step 1: Search for document
    search_result = search_engine({"query": "test document"})
    url = search_result["results"][0]["url"]

    # Step 2: Read document
    doc_result = document_query({"document": url, "queries": ["summary"]})

    # Step 3: Verify output shape
    assert "content" in doc_result
    assert len(doc_result["content"]) > 0
~~~

### Schema Validation Testing

~~~python
from jsonschema import validate, ValidationError

def test_tool_schema_compliance():
    schema = get_tool_schema("search_engine")
    valid_call = {"query": "test"}
    invalid_call = {"search_term": "test"}  # Wrong arg name

    validate(instance=valid_call, schema=schema)  # Passes

    with pytest.raises(ValidationError):
        validate(instance=invalid_call, schema=schema)  # Fails
~~~

### Mocking Dependencies

~~~python
from unittest.mock import patch

def test_search_with_mock():
    mock_response = {"results": [{"title": "Mock Result", "url": "http://mock.com"}]}

    with patch("requests.get") as mock_get:
        mock_get.return_value.json.return_value = mock_response
        result = search_engine({"query": "test"})
        assert len(result["results"]) == 1
        mock_get.assert_called_once()
~~~

### Load Testing

~~~python
import asyncio
import time

async def load_test_tool():
    """Test tool under concurrent load."""
    tasks = [search_engine({"query": f"query_{i}"}) for i in range(100)]
    start = time.time()
    results = await asyncio.gather(*tasks)
    duration = time.time() - start

    avg_latency = duration / len(results)
    success_rate = sum(1 for r in results if "error" not in r) / len(results)

    print(f"Avg latency: {avg_latency:.3f}s")
    print(f"Success rate: {success_rate:.1%}")
    assert avg_latency < 2.0, "Latency too high"
    assert success_rate > 0.95, "Success rate too low"
~~~

## 9. Anti-patterns

Recognize and eliminate these common tool design failures.

### Overly Complex Tools

**Symptom:** Tool description exceeds 5 sentences. Agent frequently misuses the tool.

**Fix:** Split into smaller tools with single responsibilities.

~~~python
# ANTI-PATTERN: God tool
def manage_data(action, source, format, filter, sort, limit, output, transform):
    """Manage data from various sources with multiple operations."""
    ...

# FIX: Atomic tools
def load_data(source: str, format: str) -> DataFrame: ...
def filter_data(data: DataFrame, conditions: dict) -> DataFrame: ...
def transform_data(data: DataFrame, operations: list) -> DataFrame: ...
def export_data(data: DataFrame, format: str, path: str) -> str: ...
~~~

### Inconsistent Naming

**Symptom:** Multiple verbs for same action (`get_user`, `fetch_user`, `retrieve_user`).

**Fix:** Establish verb taxonomy and enforce consistently.

### Missing Validation

**Symptom:** Tool crashes with unhandled exceptions on invalid input.

**Fix:** Validate all inputs against schema before execution. Return structured errors.

~~~python
# ANTI-PATTERN: No validation
def read_file(path):
    return open(path).read()  # Crashes on missing file

# FIX: Validation with structured error
def read_file(path: str) -> dict:
    if not path.startswith("/"):
        return {"error": {"code": "VALIDATION_ERROR", "message": "Path must be absolute"}}
    try:
        with open(path) as f:
            return {"content": f.read()}
    except FileNotFoundError:
        return {"error": {"code": "NOT_FOUND", "message": f"File not found: {path}"}}
~~~

### Silent Failures

**Symptom:** Tool returns success but operation failed. Agent proceeds with bad state.

**Fix:** Always return explicit success/failure status. Never swallow exceptions.

### Tool Coupling

**Symptom:** Tool A requires output from Tool B in a specific format.

**Fix:** Tools should be independently callable. Use intermediate data formats.

### God Tools

**Symptom:** Single tool handles multiple domains (e.g., `do_thing` that creates, updates,
deletes, and queries based on an `action` parameter with 10+ values).

**Fix:** Split by domain. Use the 80/20 rule: if 80% of calls use 20% of the tool's
functionality, extract that into a dedicated tool.

### Parameter Bloat

**Symptom:** Tool has >10 parameters, most optional.

**Fix:** Group related parameters into objects. Split tools by use case.

~~~python
# ANTI-PATTERN: Parameter bloat
def create_user(name, email, role, department, manager, location, phone, title,
                start_date, salary, benefits, permissions, notifications, timezone):
    ...

# FIX: Grouped parameters
def create_user(identity: dict, employment: dict, preferences: dict) -> User:
    """Create user with grouped parameter objects."""
    ...
~~~

## Quick Reference: Tool Design Checklist

| Check | Question | Pass/Fail |
|-------|----------|-----------|
| Atomicity | Does this tool do one thing? | |
| Naming | Is the name verb-noun, snake_case, unambiguous? | |
| Schema | Are required args marked? Types specified? Defaults provided? | |
| Description | Can an agent use this tool from description alone? | |
| Errors | Are errors structured with codes and messages? | |
| Validation | Are all inputs validated before execution? | |
| Idempotency | Is the tool idempotent or is non-idempotency documented? | |
| Observability | Is the tool invocation logged? | |
| Testing | Are unit, integration, and schema tests written? | |
| Size | Does the tool have <8 parameters and <3 sentence description? | |

## Workflow: Designing a New Tool

1. **Define purpose** — What single operation does this tool perform?
2. **Classify** — Read, Write, Execute, or Communicate?
3. **Name** — Verb-noun, snake_case, consistent with existing tools
4. **Schema** — Define required/optional args, types, defaults, constraints
5. **Description** — Write 1-2 sentence description enabling agent self-service
6. **Error cases** — Enumerate failure modes and error codes
7. **Example** — Provide JSON call example
8. **Tests** — Write unit tests for happy path, edge cases, and error conditions
9. **Register** — Add to tool registry with prompt documentation
10. **Review** — Run through anti-pattern checklist

## Workflow: Auditing Existing Tools

1. **Inventory** — List all tools with names, descriptions, parameter counts
2. **Overlap analysis** — Identify tools with >50% argument similarity
3. **Usage analysis** — Check invocation frequency; flag unused tools
4. **Error analysis** — Review error logs for frequent failure modes
5. **Consolidation candidates** — Identify merge/split opportunities
6. **Schema audit** — Verify all schemas match implementation
7. **Description audit** — Verify descriptions enable correct agent usage
8. **Test coverage** — Verify all tools have unit and integration tests
9. **Report** — Document findings with prioritized recommendations
