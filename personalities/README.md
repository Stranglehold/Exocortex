# Personality Loader

Drop AIEOS-format JSON files into `/a0/usr/personalities/`.

## Selection priority:
1. `personality_file` setting in settings.json (e.g. "major_zero.json")
2. `_active.json` if it exists
3. First .json file alphabetically

## Swapping personalities:
- Drop a new JSON file in the directory
- Either rename it to `_active.json` or set `personality_file` in settings
- Restart the agent

## Format:
Uses the AIEOS v1.1 schema (https://aieos.org/schema/v1.1)
See David_MajorZero.json for an example.
