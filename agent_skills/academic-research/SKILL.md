---
name: "academic-research"
description: "Structured access to academic literature via Semantic Scholar API. Search papers, get citation counts, retrieve abstracts, find authors. Free, no API key required for basic use."
version: "1.0.0"
author: "agent"
tags: ["research", "academic", "papers", "citations", "semantic-scholar"]
trigger_patterns:
  - "search academic papers"
  - "find research papers on"
  - "look up citations for"
  - "find papers by author"
  - "academic literature on"
---

# Academic Research Skill

## Overview
Access to Semantic Scholar API for academic paper search, metadata retrieval, citations, and author information. Free API requiring no key for basic usage.

## Base URL
```
https://api.semanticscholar.org/graph/v1/
```

## Key Endpoints

### Paper Search
```python
GET /paper/search?query=<search_terms>&limit=<count>
```

**Parameters:**
- `query` (required): Search terms
- `limit` (optional, default 10, max 200): Number of results
- `fields` (optional): Fields to return
- `offset` (optional): Pagination offset
- `yearLow`/`yearHigh`: Year range filter
- `venue` (optional): Filter by venue/conference

**Example Response:**
```json
{
  "data": [
    {
      "title": "Attention Is All You Need",
      "abstract": "The dominant sequence transduction models...",
      "authors": [{"name": "Ashish Vaswani"}, {"name": "Noam Shazeer"}],
      "year": 2017,
      "venue": "NeurIPS",
      "citationCount": 95000,
      "id": "SEMGRX8QFV",
      "url": "https://doi.org/10.48550/arXiv.1706.03762"
    }
  ],
  "total": 1500
}
```

### Paper Details by ID
```python
GET /paper/{id}
```

**Example:** `https://api.semanticscholar.org/graph/v1/paper/SEMGRX8QFV`

### Author Search
```python
GET /author/search?query=<name>&limit=<count>
```

## Usage Examples

### Basic Paper Search
```python
import urllib.request
import json

def search_papers(query, limit=10):
    url = f"https://api.semanticscholar.org/graph/v1/paper/search"
    params = f"?query={urllib.parse.quote(query)}&limit={limit}"

    req = urllib.request.Request(url + params)
    req.add_header("User-Agent", "Mozilla/5.0")

    with urllib.request.urlopen(req, timeout=15) as response:
        return json.loads(response.read().decode())

# Search for transformer papers
results = search_papers("transformer neural network", limit=5)
for paper in results["data"]:
    print(f"{paper['title']} ({paper['year']}) - {paper['citationCount']} citations")
```

### Get Paper with Citations
```python
def get_paper_with_citations(paper_id, citation_limit=10):
    # Get paper details
    url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}"
    req = urllib.request.Request(url)

    with urllib.request.urlopen(req) as response:
        paper = json.loads(response.read().decode())

    # Get citing papers
    citations_url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}/citations"
    citations_url += f"?limit={citation_limit}&fields=title,year,citationCount"

    with urllib.request.urlopen(citations_url) as response:
        paper["citingPapers"] = json.loads(response.read().decode())

    return paper
```

### Author Search and Papers
```python
def find_author_papers(author_name, limit=10):
    # Search for author
    url = f"https://api.semanticscholar.org/graph/v1/author/search"
    url += f"?query={urllib.parse.quote(author_name)}&limit=1"

    with urllib.request.urlopen(url) as response:
        authors = json.loads(response.read().decode())

    if not authors.get("data"):
        return None

    author_id = authors["data"][0]["id"]

    # Get author's papers
    papers_url = f"https://api.semanticscholar.org/graph/v1/author/{author_id}/papers"
    papers_url += f"?limit={limit}&fields=title,year,citationCount,venue"

    with urllib.request.urlopen(papers_url) as response:
        return json.loads(response.read().decode())
```

## Error Handling and Rate Limits

### Rate Limit Information
- **Free tier**: ~150 requests/hour (no API key)
- **With API key**: Higher limits available
- **Error code**: HTTP 429 when rate limited

### Robust Implementation with Retry
```python
import time
from urllib import request, error

def fetch_with_retry(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            req = request.Request(url)
            req.add_header("User-Agent", "Mozilla/5.0")

            with request.urlopen(req, timeout=15) as response:
                return json.loads(response.read().decode())

        except error.HTTPError as e:
            if e.code == 429:  # Rate limited
                wait_time = (attempt + 1) * 5
                print(f"Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
    return None
```

## Common Use Cases

### Find Highly-Cited Papers on Topic
```python
def find_top_cited_papers(topic, min_citations=1000):
    results = search_papers(topic, limit=200)

    # Sort by citation count
    papers = sorted(
        results["data"],
        key=lambda p: p.get("citationCount", 0),
        reverse=True
    )

    return [p for p in papers if p.get("citationCount", 0) >= min_citations][:10]
```

### Get Papers from Specific Venue/Year
```python
def get_papers_by_venue_year(venue, year):
    url = f"https://api.semanticscholar.org/graph/v1/paper/search"
    url += f"?query=&limit=200&fields=title,authors,citationCount"

    with urllib.request.urlopen(url) as response:
        all_papers = json.loads(response.read().decode())["data"]

    # Filter client-side (API doesn't support complex filters well)
    filtered = [
        p for p in all_papers
        if str(p.get("year", "")).startswith(str(year))
        and venue.lower() in str(p.get("venue", "")).lower()
    ]

    return filtered[:50]
```

## Notes
- API is free but rate-limited without an API key
- Apply for API key at: https://www.semanticscholar.org/product/api#api-key-form
- Response format may vary slightly between endpoints
- Some fields may be null/missing depending on data availability