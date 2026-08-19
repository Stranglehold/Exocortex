---
name: "web-research-macro"
description: "Unified web research pipeline combining browser navigation, content sanitization, and document extraction into a single call. Use when you need to extract clean text from websites requiring JavaScript rendering or login."
version: "1.0.0"
author: "agent"
tags: ["web", "research", "scraping", "extraction", "pipeline"]
trigger_patterns:
  - "extract content from website"
  - "scrape webpage text"
  - "get clean text from url"
  - "research website content"
---

# Web Research Macro Skill

## Overview
A unified skill that orchestrates browser_agent, content-sanitizer, and document_query into a single pipeline call. Extracts clean, safe text from websites requiring JavaScript rendering, handles logins, strips dangerous scripts, and returns sanitized content.

## Architecture
```
URL Input → Browser Agent (render + extract HTML) → Content Sanitizer (strip scripts, detect injections) → Document Query (extract text) → Clean Output
```

## Capabilities
- **JavaScript Rendering**: Executes JS via Playwright browser_agent
- **Login Handling**: Supports authentication flows
- **Content Sanitization**: Strips scripts, iframes, event handlers
- **Injection Detection**: Identifies prompt injection attempts
- **Text Extraction**: Returns clean text only, no HTML

## Usage

### Basic Usage
```python
from web_research import WebResearchMacro

researcher = WebResearchMacro()
result = researcher.extract("https://example.com/article")
print(result["clean_text"])  # Sanitized text content
print(result["is_safe"])     # True if no injection detected
```

### With Login Support
```python
result = researcher.extract(
    url="https://example.com/protected",
    login_url="https://example.com/login",
    username_selector="#username",
    password_selector="#password",
    submit_selector="#login-btn",
    credentials={"user": "myuser", "pass": "mypassword"}
)
```

### Batch Extraction
```python
urls = [
    "https://site1.com/article1",
    "https://site2.com/article2",
]
results = researcher.batch_extract(urls)
for url, data in results.items():
    print(f"{url}: {len(data['clean_text'])} chars")
```

## Output Format
```python
{
    "url": "https://example.com",
    "clean_text": "Extracted and sanitized text content...",
    "is_safe": True,
    "warnings": [],  # Any detected issues
    "metadata": {
        "title": "Page Title",
        "word_count": 1234,
        "extraction_time_ms": 5678
    }
}
```

## Dependencies
```bash
pip install playwright beautifulsoup4
playwright install chromium
```

## When to Use
- Extracting content from JavaScript-heavy websites
- Research tasks requiring multiple website visits
- Situations where raw HTML contains dangerous scripts
- Need for clean text without manual sanitization steps
