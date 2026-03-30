---
name: "web-research-macro"
description: "Workflow methodology for extracting clean text from websites. Sequences browser_agent, inline sanitization, and document_query into a repeatable pipeline. Not an importable module — a pattern for calling tools that already exist."
version: "1.1.0"
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

A workflow methodology — **not an importable module** — that sequences `browser_agent`, inline content sanitization, and `document_query` to extract clean, safe text from websites. Follow this pattern; don't try to import it.

## Pipeline

```
URL Input
   ↓
browser_agent  (render JS, handle logins, return HTML)
   ↓
Inline sanitization  (strip scripts/iframes, detect injection)
   ↓
document_query  (extract clean text)
   ↓
Clean Output
```

## Step-by-Step Usage

### Basic Extraction

```python
import re

# Step 1: Render the page
result = browser_agent(
    url="https://example.com/article",
    task="Navigate to this URL and return the full page HTML content."
)
html = result.get("html", result.get("content", str(result)))

# Step 2: Sanitize inline
html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL|re.IGNORECASE)
html = re.sub(r'<iframe[^>]*>.*?</iframe>', '', html, flags=re.DOTALL|re.IGNORECASE)
html = re.sub(r'\bon\w+\s*=\s*["\'][^"\']*["\']', '', html, flags=re.IGNORECASE)

injection_patterns = [
    r'ignore (previous|all|above) instructions',
    r'you are now', r'new persona', r'disregard', r'system prompt'
]
is_safe = not any(re.search(p, html, re.IGNORECASE) for p in injection_patterns)
if not is_safe:
    print("WARNING: Possible prompt injection detected in page content")

# Step 3: Extract text
text_result = document_query(document=html, query="Extract all readable text content")
clean_text = text_result.get("text", str(text_result))
```

### With Login

```python
result = browser_agent(
    url="https://example.com/protected",
    task="""
    1. Go to https://example.com/login
    2. Enter credentials in the login form
    3. Submit and navigate to https://example.com/protected
    4. Return the full page HTML
    """
)
# Then sanitize and extract as above
```

### Batch Extraction

```python
urls = ["https://site1.com/article1", "https://site2.com/article2"]
results = {}
for url in urls:
    try:
        r = browser_agent(url=url, task="Return full page HTML content")
        html = r.get("html", str(r))
        # sanitize (see above)
        results[url] = {"clean_text": clean_text, "is_safe": is_safe}
    except Exception as e:
        results[url] = {"error": str(e)}
```

## Output

```python
{
    "url": "https://example.com",
    "clean_text": "Extracted and sanitized text...",
    "is_safe": True,       # False if injection patterns found
    "warnings": []
}
```

## When to Use
- JS-heavy sites that don't render without a browser
- Sites requiring login before content is accessible
- Any source where prompt injection is a concern

## When NOT to Use
- Simple static pages: `search_engine` is faster
- PDFs: use `document_query` directly on the file
