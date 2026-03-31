---
name: "config-edit"
description: "Safely edit configuration files (YAML, JSON, TOML, INI) with validation and backup. Use when users need to modify settings, add new configurations, or update existing config values in their projects."
author: "agent"
---
# Config Edit Skill

## Purpose
Provides safe, validated editing of configuration files across multiple formats (YAML, JSON, TOML, INI) with automatic backup creation and syntax validation. Helps users modify settings without introducing errors.

## When to Use
- User wants to edit a configuration file in their project
- Need to add/update/delete specific config keys or values
- User requests changes to YAML, JSON, TOML, or INI files
- Configuration migration or transformation is needed

## Instructions

### Step 1: Identify the Config File and Format
Determine which config file(s) need editing:
- Check common locations: `config.yaml`, `.env`, `settings.json`, `pyproject.toml`, etc.
- Ask user if unclear which file to modify
- Detect format from extension or content

### Step 2: Read Current Configuration
Use the appropriate parser based on format:
```python
# YAML
import yaml
with open(filepath, 'r') as f:
    config = yaml.safe_load(f)

# JSON
import json
with open(filepath, 'r') as f:
    config = json.load(f)

# TOML
import tomllib  # Python 3.11+
or import toml  # pip install toml
with open(filepath, 'rb') as f:
    config = tomllib.load(f)

# INI
import configparser
config = configparser.ConfigParser()
config.read(filepath)
```

### Step 3: Create Backup
Always create a timestamped backup before modifications:
```python
from datetime import datetime
backup_path = f"{filepath}.{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
import shutil
shutil.copy2(filepath, backup_path)
print(f"Backup created: {backup_path}")
```

### Step 4: Make Modifications
Apply the requested changes to the config object:
- For nested keys, traverse the structure carefully
- Preserve existing comments when possible (note: most parsers strip comments)
- Handle type conversions appropriately

### Step 5: Validate Changes
Before writing:
```python
# Re-parse to validate syntax
if format == 'yaml':
    yaml.safe_load(yaml.dump(config))  # Validates round-trip
elif format == 'json':
    json.loads(json.dumps(config, indent=2))
elif format == 'toml':
    import tomlkit
    tomlkit.dumps(config)
```

### Step 6: Write Modified Config
```python
# YAML
with open(filepath, 'w') as f:
    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

# JSON
with open(filepath, 'w') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

# TOML (requires tomlkit for pretty output)
import tomlkit
doc = tomlkit.document()
# ... populate doc ...
with open(filepath, 'w') as f:
    f.write(tomlkit.dumps(doc))

# INI
with open(filepath, 'w') as f:
    config.write(f)
```

### Step 7: Verify and Report
- Read back the file to confirm changes were written correctly
- Show user a diff or summary of what changed
- Provide instructions for reverting from backup if needed

## Output Format
After editing, provide:
1. **File edited**: Path to the configuration file
2. **Changes made**: Summary of modifications (keys added/updated/deleted)
3. **Backup location**: Where the backup was saved
4. **Verification**: Confirmation that file is valid and readable
5. **Revert instructions**: How to restore from backup if needed

## Example Usage Patterns

### Edit YAML Config
```python
import yaml

# Read
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Modify
config["database"]["host"] = "new-host.example.com"
config.setdefault("logging", {})["level"] = "DEBUG"

# Write with validation
yaml.dump(config, open('config.yaml', 'w'), default_flow_style=False)
```

### Edit JSON Config
```python
import json

with open('settings.json', 'r') as f:
    config = json.load(f)

config["features"]["new_feature"] = True
del config["deprecated_key"]

with open('settings.json', 'w') as f:
    json.dump(config, f, indent=2)
```

### Edit TOML Config
```python
import tomlkit

doc = tomlkit.parse(open('pyproject.toml').read())
doc["tool"]["ruff"]["line-length"] = 120

with open('pyproject.toml', 'w') as f:
    f.write(tomlkit.dumps(doc))
```

## Error Handling
- Catch and report syntax errors clearly
- Preserve original file on error (backup already exists)
- Provide helpful messages about what went wrong
- Suggest corrections when possible

## Notes
- Most config parsers strip comments; warn users if comment preservation is critical
- For complex edits, consider showing a preview before applying
- Some formats (like .env files) may need custom parsing for variable expansion
