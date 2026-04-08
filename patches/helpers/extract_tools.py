import re, os, importlib, importlib.util, inspect
from types import ModuleType
from typing import Any, Type, TypeVar
from .dirty_json import DirtyJson
from .files import get_abs_path, deabsolute_path
import regex
from fnmatch import fnmatch

# Gemma 4 / native LLM tool call format:
#   <|tool_call>call:TOOL_NAME{arg: "val", ...}<tool_call|>
# May be preceded by <channel|> or other tokens.
_NATIVE_TOOL_CALL_RX = re.compile(
    r'<\|tool_call\>\s*call\s*:\s*(\w+)\s*(\{)',
    re.IGNORECASE,
)


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


def json_parse_dirty(json:str) -> dict[str,Any] | None:
    if not json or not isinstance(json, str):
        return None

    stripped = json.strip()

    # ── Native tool call format (Gemma 4, etc.) ───────────────────────────
    # Pattern: <|tool_call>call:TOOL_NAME{arg: "val", ...}<tool_call|>
    # Detect before standard JSON path — args dict has no tool_name key.
    m = _NATIVE_TOOL_CALL_RX.search(stripped)
    if m:
        tool_name = m.group(1)
        # m.group(2) == '{'; start from the { character
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
    ext_json = extract_json_object_string(stripped)
    if ext_json:
        try:
            data = DirtyJson.parse_string(ext_json)
            if isinstance(data, dict):
                # Valid JSON but empty tool_name — model emitted {"tool_name": "", ...}
                # after reasoning tokens. Treat the original text as a plain response
                # rather than routing to Unknown and dumping the full tool list.
                if not data.get("tool_name", "").strip():
                    return {"tool_name": "response", "tool_args": {"text": stripped}}
                return data
        except Exception:
            # If parsing fails, fall through to plain-text fallback
            pass

    # Fallback: plain text → implicit response tool call.
    # Reasoning-distilled models respond in natural language after thinking tokens
    # rather than JSON. Wrapping as a response call avoids the misformat loop.
    if stripped:
        return {"tool_name": "response", "tool_args": {"text": stripped}}
    return None

def extract_json_object_string(content):
    start = content.find('{')
    if start == -1:
        return ""

    # Find the first '{'
    end = content.rfind('}')
    if end == -1:
        # If there's no closing '}', return from start to the end
        return content[start:]
    else:
        # If there's a closing '}', return the substring from start to end
        return content[start:end+1]

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
        return match.group(0).replace('\n', '\\n')

    # Use regex to find string values and apply the replacement function
    fixed_string = re.sub(r'(?<=: ")(.*?)(?=")', replace_unescaped_newlines, json_string, flags=re.DOTALL)
    return fixed_string


T = TypeVar('T')  # Define a generic type variable

def import_module(file_path: str) -> ModuleType:
    # Handle file paths with periods in the name using importlib.util
    abs_path = get_abs_path(file_path)
    module_name = os.path.basename(abs_path).replace('.py', '')

    # Create the module spec and load the module
    spec = importlib.util.spec_from_file_location(module_name, abs_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {abs_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def load_classes_from_folder(folder: str, name_pattern: str, base_class: Type[T], one_per_file: bool = True) -> list[Type[T]]:
    classes = []
    abs_folder = get_abs_path(folder)

    # Get all .py files in the folder that match the pattern, sorted alphabetically
    py_files = sorted(
        [file_name for file_name in os.listdir(abs_folder) if fnmatch(file_name, name_pattern) and file_name.endswith(".py")]
    )

    # Iterate through the sorted list of files
    for file_name in py_files:
        file_path = os.path.join(abs_folder, file_name)
        # Use the new import_module function
        module = import_module(file_path)

        # Get all classes in the module
        class_list = inspect.getmembers(module, inspect.isclass)

        # Filter for classes that are subclasses of the given base_class
        # iterate backwards to skip imported superclasses
        for cls in reversed(class_list):
            if cls[1] is not base_class and issubclass(cls[1], base_class):
                classes.append(cls[1])
                if one_per_file:
                    break

    return classes

def load_classes_from_file(file: str, base_class: type[T], one_per_file: bool = True) -> list[type[T]]:
    classes = []
    # Use the new import_module function
    module = import_module(file)

    # Get all classes in the module
    class_list = inspect.getmembers(module, inspect.isclass)

    # Filter for classes that are subclasses of the given base_class
    # iterate backwards to skip imported superclasses
    for cls in reversed(class_list):
        if cls[1] is not base_class and issubclass(cls[1], base_class):
            classes.append(cls[1])
            if one_per_file:
                break

    return classes
