# Content Sanitizer Skill

## Overview
Insulating layer between raw web content and agent context. Protects against prompt injection attacks by sanitizing HTML, detecting adversarial patterns, and extracting only safe text.

## Capabilities
- **HTML Sanitization**: Strips scripts, iframes, event handlers, dangerous elements
- **Instruction Detection**: Identifies common prompt injection patterns
- **Safe Fetching**: Bounded extraction of web content with automatic sanitization
- **Content Flagging**: Reports suspicious patterns without exposing raw data

## Usage
```python
from skills.content_sanitizer.sanitizer import ContentSanitizer

# Sanitize HTML/text
result = ContentSanitizer.clean(raw_html_or_text)
print(f"Safe: {result.is_safe()}")
print(result.clean_text)  # Only safe text content
```

## Architecture
Raw Web Content → Content Sanitizer (Insulation Layer) → Safe Text Only
                    ↓
            • Strips scripts/iframes
            • Removes event handlers  
            • Detects instruction patterns
            • Extracts text only
