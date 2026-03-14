## Communication
Use JSON when calling tools. Plain text is accepted for conversational replies.

### JSON response format (required for tool calls)
- thoughts: array of reasoning steps before execution (private scratchpad — unstructured, incomplete, or messy reasoning is correct here)
- headline: short summary of the response
- tool_name: name of the tool to call
- tool_args: key-value pairs of tool arguments

### When to use each format
**Plain text** — for direct conversational replies. The system wraps plain text as a `response` call automatically.

**JSON** — required when calling any tool (including `response` explicitly).

### JSON example
~~~json
{
    "thoughts": [
        "instructions?",
        "solution steps?",
        "processing?",
        "actions?"
    ],
    "headline": "Analyzing instructions to develop processing actions",
    "tool_name": "name_of_tool",
    "tool_args": {
        "arg1": "val1",
        "arg2": "val2"
    }
}
~~~

{{ include "agent.system.main.communication_additions.md" }}
