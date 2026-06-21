"""
Wiki Knowledge Retriever — Search and surface accumulated wiki knowledge
========================================================================
Utility module for the Exocortex wiki integration.

Provides functions to search the wiki by keyword, retrieve relevant pages,
and format them for injection into agent/subagent context.

Used by:
- program.md guidance ("search your wiki before knowledge-intensive work")
- Orchestrating agents before subagent delegation
- The methodology tracker for wiki-augmented cycle tracking
- Future: the incubation engine's collision detector

Design: Opus — Wiki Integration spec, June 2026
Pattern source: Karpathy's LLM Wiki (April 2026) + Hermes Agent wiki skill
"""

import os
import re
from typing import List, Tuple, Optional

WIKI_ROOT = "/a0/usr/workdir/workspace/wiki"
WIKI_INDEX = os.path.join(WIKI_ROOT, "index.md")
WIKI_RESEARCH = os.path.join(WIKI_ROOT, "research")
WIKI_PAGES = os.path.join(WIKI_ROOT, "pages")

# Maximum pages to surface per query
MAX_PAGES = 3
# Maximum characters per page summary
MAX_PAGE_CHARS = 2000
# Minimum word length for keyword matching (skip stop words)
MIN_WORD_LEN = 4


def search_wiki(query: str, max_results: int = MAX_PAGES) -> List[dict]:
    """
    Search the wiki for pages relevant to a query.
    
    Uses keyword matching against filenames and index entries.
    Returns list of {path, title, relevance_score, snippet} dicts,
    sorted by relevance.
    
    Args:
        query: Natural language query or topic keywords
        max_results: Maximum pages to return
    
    Returns:
        List of matching wiki page metadata
    """
    query_words = _extract_keywords(query)
    if not query_words:
        return []
    
    scored_pages = []
    
    # Score pages from the research directory (where most content lives)
    for directory in [WIKI_RESEARCH, WIKI_PAGES, WIKI_ROOT]:
        if not os.path.isdir(directory):
            continue
        for filename in os.listdir(directory):
            if not filename.endswith('.md'):
                continue
            filepath = os.path.join(directory, filename)
            score = _score_page(filepath, filename, query_words)
            if score > 0:
                title = _extract_title(filepath, filename)
                scored_pages.append({
                    "path": filepath,
                    "filename": filename,
                    "title": title,
                    "score": score,
                })
    
    # Also check the index for title-based matches
    index_matches = _search_index(query_words)
    for match in index_matches:
        # Boost score for pages found in index
        for page in scored_pages:
            if match["filename"] in page["path"]:
                page["score"] += 2
        # Add pages found only in index
        if not any(match["filename"] in p["path"] for p in scored_pages):
            scored_pages.append(match)
    
    # Sort by score descending
    scored_pages.sort(key=lambda x: x["score"], reverse=True)
    
    return scored_pages[:max_results]


def retrieve_wiki_context(query: str, max_results: int = MAX_PAGES, 
                          max_chars: int = MAX_PAGE_CHARS) -> str:
    """
    Search wiki and return formatted context string ready for injection.
    
    This is the main entry point for wiki-augmented generation.
    Returns a formatted block of relevant wiki content that can be
    prepended to a subagent's instructions or injected into context.
    
    Args:
        query: The task or topic to search for
        max_results: Maximum pages to include
        max_chars: Maximum characters per page
    
    Returns:
        Formatted string with wiki context, or empty string if no matches
    """
    pages = search_wiki(query, max_results)
    if not pages:
        return ""
    
    sections = ["[WIKI KNOWLEDGE — from your accumulated research, use to inform your work]"]
    
    for page in pages:
        content = _read_page_summary(page["path"], max_chars)
        if content:
            sections.append(f"\n### {page['title']}\n{content}")
    
    if len(sections) == 1:
        return ""  # No content found despite filename matches
    
    sections.append("\n[END WIKI KNOWLEDGE — cite pages used in your response]")
    return "\n".join(sections)


def list_wiki_topics() -> List[str]:
    """
    Return a list of all wiki page titles for index/discovery.
    """
    topics = []
    for directory in [WIKI_RESEARCH, WIKI_PAGES]:
        if not os.path.isdir(directory):
            continue
        for filename in os.listdir(directory):
            if filename.endswith('.md'):
                title = _extract_title(os.path.join(directory, filename), filename)
                topics.append(title)
    return sorted(topics)


# === Internal helpers ===

def _extract_keywords(text: str) -> set:
    """Extract meaningful keywords from a query string."""
    words = re.split(r'[^a-z0-9]+', text.lower())
    return {w for w in words if len(w) >= MIN_WORD_LEN}


def _score_page(filepath: str, filename: str, query_words: set) -> int:
    """
    Score a page's relevance to query keywords.
    Checks filename (cheap) then first 500 chars of content (slightly more expensive).
    """
    score = 0
    
    # Filename matching (most pages have descriptive filenames)
    name_words = set(re.split(r'[^a-z0-9]+', filename.lower().replace('.md', '')))
    name_overlap = query_words & name_words
    score += len(name_overlap) * 3  # Filename matches weighted heavily
    
    # Content header matching (first 500 chars — title, description, frontmatter)
    if score == 0:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                header = f.read(500).lower()
            header_words = set(re.split(r'[^a-z0-9]+', header))
            content_overlap = query_words & header_words
            score += len(content_overlap)
        except Exception:
            pass
    
    return score


def _search_index(query_words: set) -> List[dict]:
    """Search the wiki index.md for matching entries."""
    matches = []
    if not os.path.exists(WIKI_INDEX):
        return matches
    
    try:
        with open(WIKI_INDEX, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line_lower = line.lower()
                line_words = set(re.split(r'[^a-z0-9]+', line_lower))
                overlap = query_words & line_words
                if len(overlap) >= 2:  # Require at least 2 keyword matches
                    # Extract filename from markdown link
                    link_match = re.search(r'\[.*?\]\((.*?\.md)\)', line)
                    if link_match:
                        rel_path = link_match.group(1)
                        full_path = os.path.join(WIKI_ROOT, rel_path)
                        title = _extract_title_from_line(line)
                        matches.append({
                            "path": full_path,
                            "filename": os.path.basename(rel_path),
                            "title": title,
                            "score": len(overlap),
                        })
    except Exception:
        pass
    
    return matches


def _extract_title(filepath: str, filename: str) -> str:
    """Extract the title from a wiki page (first # heading or filename)."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if line.startswith('# ') and not line.startswith('## '):
                    return line[2:].strip()
                # Also check frontmatter description
                if line.startswith('description:'):
                    desc = line.split(':', 1)[1].strip().strip('"').strip("'")
                    if desc and len(desc) > 10:
                        return desc[:100]
    except Exception:
        pass
    # Fallback: humanize the filename
    return filename.replace('.md', '').replace('-', ' ').replace('_', ' ').title()


def _extract_title_from_line(index_line: str) -> str:
    """Extract title from an index.md line like '- [name](path) — Title'."""
    parts = index_line.split('—')
    if len(parts) >= 2:
        return parts[1].strip().rstrip('|').strip().rstrip('*').strip()
    # Try the link text
    match = re.search(r'\[(.*?)\]', index_line)
    if match:
        return match.group(1).replace('-', ' ').title()
    return index_line.strip()


def _read_page_summary(filepath: str, max_chars: int = MAX_PAGE_CHARS) -> str:
    """
    Read the first max_chars of a wiki page, skipping frontmatter.
    Returns the content body (not YAML frontmatter).
    """
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception:
        return ""
    
    # Skip YAML frontmatter (between --- markers)
    if content.startswith('---'):
        end_fm = content.find('---', 3)
        if end_fm > 0:
            content = content[end_fm + 3:].strip()
    
    # Return first max_chars
    if len(content) > max_chars:
        # Try to break at a paragraph boundary
        truncation_point = content.rfind('\n\n', 0, max_chars)
        if truncation_point > max_chars // 2:
            content = content[:truncation_point] + "\n[... truncated]"
        else:
            content = content[:max_chars] + "\n[... truncated]"
    
    return content
