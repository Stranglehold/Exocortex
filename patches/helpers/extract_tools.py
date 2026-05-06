from .dirty_json import DirtyJson
import regex, re
from helpers.modules import load_classes_from_file, load_classes_from_folder # keep here for backwards compatibility
from typing import Any

# Gemma 4 / native LLM tool call format:
#   <|tool_call>call:TOOL_NAME{arg: "val", ...}<tool_call|>
_NATIVE_TOOL_CALL_RX = re.compile(
    r'<\|tool_call\>\s*call\s*:\s*(\w+)\s*(\{)',
    re.IGNORECASE,
)

# Strip thinking-token blocks that leak from reasoning-distilled models before JSON parse.
_THINK_TAG_RX = re.compile(r'<think(?:ing)?>\s*.*?\s*</think(?:ing)?>', re.DOTALL | re.IGNORECASE)

# Extract tool_name from partial / unparseable JSON via regex fallback.
_PARTIAL_TOOL_NAME_RX = re.compile(r'"tool_name"\s*:\s*"([^"]+)"')

# Extract text field value from a partial (truncated) response tool JSON.
_PARTIAL_TEXT_RX = re.compile(r'"text"\s*:\s*"(.*)', re.DOTALL)

# Tools that carry large inline payloads likely to trigger output-token truncation.
_LARGE_PAYLOAD_TOOLS = {"code_execution_tool", "text_editor:write", "text_editor"}

# Minimum partial size (chars) before attempting response-tool truncation recovery.
_RESPONSE_RECOVERY_THRESHOLD = 8000


def _find_closing_brace(s: str) -> int:
    """Return index of the } that closes the { at s[0]. Returns -1 if not found."""
    if not s or s[0] != '{':
        return -1
    depth = 0
    in_str = False
    escape = False
    for i, ch in enumerate(s):
        if escape:
            escape = False
            continue
        if ch == '\\' and in_str:
            escape = True
            continue
        if ch == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return i
    return -1


def _detect_truncation(partial: str) -> str | None:
    """Return the likely tool_name if partial looks like a truncated JSON payload."""
    m = _PARTIAL_TOOL_NAME_RX.search(partial)
    if not m:
        return None
    tool = m.group(1)
    if tool in _LARGE_PAYLOAD_TOOLS:
        return tool
    if '"code"' in partial or '"content"' in partial:
        return tool
    return None


def _extract_partial_response_text(partial: str) -> str | None:
    """Extract the 'text' field from a partial (truncated) response tool JSON."""
    m = _PARTIAL_TEXT_RX.search(partial)
    if not m:
        return None
    raw = m.group(1)
    text = (raw
        .replace('\\n', '\n')
        .replace('\\t', '\t')
        .replace('\\"', '"')
        .replace('\\\\', '\\')
    )
    if text.endswith('\\'):
        text = text[:-1]
    return text.strip() or None


def json_parse_dirty(json: str) -> dict[str, Any] | None:
    if not json or not isinstance(json, str):
        return None

    stripped = json.strip()

    # Strip thinking tokens — reasoning-distilled models sometimes leak <think>...</think>
    stripped = _THINK_TAG_RX.sub('', stripped).strip()
    if not stripped:
        return None

    # ── Native tool call format (Gemma 4, etc.) ───────────────────────────
    m = _NATIVE_TOOL_CALL_RX.search(stripped)
    if m:
        tool_name = m.group(1)
        args_start = m.start(2)
        args_str = stripped[args_start:]
        end_idx = _find_closing_brace(args_str)
        args_json = args_str[:end_idx + 1] if end_idx >= 0 else extract_json_object_string(args_str)
        tool_args = {}
        if args_json:
            try:
                parsed = DirtyJson.parse_string(args_json)
                if isinstance(parsed, dict):
                    tool_args = parsed
            except Exception:
                pass
        return {"tool_name": tool_name, "tool_args": tool_args}

    # ── Standard JSON path ────────────────────────────────────────────────
    _start = stripped.find('{')
    if _start != -1:
        _end_idx = _find_closing_brace(stripped[_start:])
        if _end_idx == -1:
            partial = stripped[_start:]
            if len(partial) >= _RESPONSE_RECOVERY_THRESHOLD:
                m_name = _PARTIAL_TOOL_NAME_RX.search(partial)
                if m_name and m_name.group(1) == "response":
                    partial_text = _extract_partial_response_text(partial)
                    if partial_text:
                        import sys
                        print(
                            f"[EXTRACT-TOOLS] Truncated response tool detected "
                            f"({len(partial)} chars). Recovering partial text.",
                            file=sys.stderr, flush=True,
                        )
                        return {
                            "tool_name": "response",
                            "tool_args": {
                                "text": (
                                    partial_text.rstrip()
                                    + "\n\n[SYSTEM NOTICE: Response truncated by token "
                                    "limit. For long content, write to a file using "
                                    "code_execution_tool first, then respond with a "
                                    "short summary and the file path.]"
                                )
                            },
                        }
            return None
        ext_json = stripped[_start : _start + _end_idx + 1]
        try:
            data = DirtyJson.parse_string(ext_json)
            if isinstance(data, dict):
                # Empty tool_name — model emitted reasoning without a valid tool call
                if not data.get("tool_name", "").strip():
                    return {"tool_name": "response", "tool_args": {"text": stripped}}
                # text_editor colon-dispatch inference
                if data.get("tool_name") == "text_editor":
                    args = data.get("tool_args", {})
                    if "content" in args:
                        data["tool_name"] = "text_editor:write"
                    elif "edits" in args:
                        data["tool_name"] = "text_editor:patch"
                    else:
                        data["tool_name"] = "text_editor:read"
                # Detect response text truncation
                if data.get("tool_name") == "response":
                    text = data.get("tool_args", {}).get("text", "")
                    if text.rstrip().endswith(":"):
                        import sys
                        print(
                            "[EXTRACT-TOOLS] Response text ends with ':' — likely truncated "
                            "by max_tokens. Appending truncation notice.",
                            file=sys.stderr, flush=True,
                        )
                        data["tool_args"]["text"] = (
                            text.rstrip()
                            + "\n\n[SYSTEM NOTICE: Response appears truncated at this point. "
                            "If you intended to write a file, use write_file first, then call "
                            "response with the file path.]"
                        )
                # Default tool_args to {} if missing or non-dict
                if not isinstance(data.get("tool_args"), dict):
                    data["tool_args"] = {}
                return data
        except Exception:
            truncated_tool = _detect_truncation(ext_json)
            if truncated_tool:
                import sys
                print(
                    f"[EXTRACT-TOOLS] Truncated JSON detected — tool: {truncated_tool}. "
                    "fw.msg_misformat.md will inject append-mode guidance.",
                    file=sys.stderr, flush=True,
                )

    # Fallback: plain text → implicit response tool call.
    # Guard: do NOT apply to strings starting with '{'.
    if stripped and not stripped.startswith('{'):
        return {"tool_name": "response", "tool_args": {"text": stripped}}
    return None


def normalize_tool_request(tool_request: Any) -> tuple[str, dict]:
    if not isinstance(tool_request, dict):
        raise ValueError("Tool request must be a dictionary")
    tool_name = tool_request.get("tool_name")
    if not tool_name or not isinstance(tool_name, str):
        tool_name = tool_request.get("tool")
    if not tool_name or not isinstance(tool_name, str):
        raise ValueError("Tool request must have a tool_name (type string) field")
    tool_args = tool_request.get("tool_args")
    if not isinstance(tool_args, dict):
        tool_args = tool_request.get("args")
    if not isinstance(tool_args, dict):
        raise ValueError("Tool request must have a tool_args (type dictionary) field")
    return tool_name, tool_args


def extract_json_root_string(content: str) -> str | None:
    if not content or not isinstance(content, str):
        return None

    start = content.find("{")
    if start == -1:
        return None
    first_array = content.find("[")
    if first_array != -1 and first_array < start:
        return None

    parser = DirtyJson()
    try:
        parser.parse(content[start:])
    except Exception:
        return None

    if not parser.completed:
        return None

    return content[start : start + parser.index]


def extract_json_object_string(content):
    start = content.find("{")
    if start == -1:
        return ""

    # Find the first '{'
    end = content.rfind("}")
    if end == -1:
        # If there's no closing '}', return from start to the end
        return content[start:]
    else:
        # If there's a closing '}', return the substring from start to end
        return content[start : end + 1]


def extract_json_string(content):
    # Regular expression pattern to match a JSON object
    pattern = r'\{(?:[^{}]|(?R))*\}|\[(?:[^\[\]]|(?R))*\]|"(?:\\.|[^"\\])*"|true|false|null|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?'

    # Search for the pattern in the content
    match = regex.search(pattern, content)

    if match:
        # Return the matched JSON string
        return match.group(0)
    else:
        return ""


def fix_json_string(json_string):
    # Function to replace unescaped line breaks within JSON string values
    def replace_unescaped_newlines(match):
        return match.group(0).replace("\n", "\\n")

    # Use regex to find string values and apply the replacement function
    fixed_string = re.sub(
        r'(?<=: ")(.*?)(?=")', replace_unescaped_newlines, json_string, flags=re.DOTALL
    )
    return fixed_string
