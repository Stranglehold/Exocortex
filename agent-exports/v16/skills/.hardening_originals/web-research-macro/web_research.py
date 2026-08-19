"""
Web Research Macro - Unified pipeline for browser navigation, content sanitization, and text extraction.

Combines:
- browser_agent: JavaScript rendering, login handling
- content-sanitizer: Script removal, injection detection  
- document_query: Text extraction from HTML/documents
"""

import time
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup
import re


class WebResearchMacro:
    """Unified web research pipeline combining browser_agent + content-sanitizer + document_query."""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.browser_session = None
    
    def extract(
        self,
        url: str,
        login_url: Optional[str] = None,
        username_selector: Optional[str] = None,
        password_selector: Optional[str] = None,
        submit_selector: Optional[str] = None,
        credentials: Optional[Dict[str, str]] = None,
        wait_for_selector: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Extract clean, sanitized text from a URL.
        
        Args:
            url: Target URL to extract content from
            login_url: Optional login page URL
            username_selector: CSS selector for username field
            password_selector: CSS selector for password field  
            submit_selector: CSS selector for submit button
            credentials: Dict with 'user' and 'pass' keys
            wait_for_selector: Selector to wait for before extraction
            
        Returns:
            Dict with clean_text, is_safe, warnings, metadata
        """
        start_time = time.time()
        warnings = []
        
        # Phase 1: Browser Agent - Navigate and render JavaScript
        html_content = self._browser_fetch(url, login_url, username_selector, 
                                          password_selector, submit_selector, credentials)
        if not html_content:
            return {
                "url": url,
                "clean_text": "",
                "is_safe": False,
                "warnings": ["Failed to fetch content from URL"],
                "metadata": {"title": "", "word_count": 0, "extraction_time_ms": 0}
            }
        
        # Wait for specific selector if provided
        if wait_for_selector:
            self._wait_for_selector(wait_for_selector)
        
        # Phase 2: Content Sanitizer - Strip dangerous elements and detect injections
        sanitized_result = self._sanitize_content(html_content)
        clean_html = sanitized_result["clean_html"]
        if not sanitized_result["is_safe"]:
            warnings.extend(sanitized_result.get("warnings", []))
        
        # Phase 3: Document Query - Extract text from cleaned HTML
        text_content, title = self._extract_text(clean_html)
        
        extraction_time = int((time.time() - start_time) * 1000)
        word_count = len(text_content.split()) if text_content else 0
        
        return {
            "url": url,
            "clean_text": text_content,
            "is_safe": sanitized_result["is_safe"],
            "warnings": warnings,
            "metadata": {
                "title": title,
                "word_count": word_count,
                "extraction_time_ms": extraction_time
            }
        }
    
    def batch_extract(self, urls: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Extract content from multiple URLs.
        
        Args:
            urls: List of URLs to extract
            
        Returns:
            Dict mapping URL to extraction result
        """
        results = {}
        for url in urls:
            try:
                results[url] = self.extract(url)
            except Exception as e:
                results[url] = {
                    "url": url,
                    "clean_text": "",
                    "is_safe": False,
                    "warnings": [f"Error: {str(e)}"],
                    "metadata": {"title": "", "word_count": 0, "extraction_time_ms": 0}
                }
        return results
    
    def _browser_fetch(
        self,
        url: str,
        login_url: Optional[str] = None,
        username_selector: Optional[str] = None,
        password_selector: Optional[str] = None,
        submit_selector: Optional[str] = None,
        credentials: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        """
        Phase 1: Use browser_agent to navigate and render JavaScript.
        Returns raw HTML content.
        """
        try:
            from playwright.sync_api import sync_playwright
            
            with sync_playwright() as p:
                # Launch browser
                self.browser_session = p.chromium.launch(headless=True)
                page = self.browser_session.new_page()
                
                # Handle login if needed
                if login_url and credentials:
                    page.goto(login_url, wait_until="domcontentloaded", timeout=self.timeout * 1000)
                    
                    # Fill credentials
                    if username_selector:
                        page.fill(username_selector, credentials.get("user", ""))
                    if password_selector:
                        page.fill(password_selector, credentials.get("pass", ""))
                    if submit_selector:
                        page.click(submit_selector)
                    
                    # Wait for navigation
                    page.wait_for_load_state("networkidle", timeout=self.timeout * 1000)
                
                # Navigate to target URL
                page.goto(url, wait_until="domcontentloaded", timeout=self.timeout * 1000)
                
                # Wait for network idle
                page.wait_for_load_state("networkidle", timeout=self.timeout * 1000)
                
                # Extract full HTML
                html_content = page.content()
                
                return html_content
                
        except Exception as e:
            print(f"Browser fetch error: {e}")
            return None
    
    def _wait_for_selector(self, selector: str) -> bool:
        """Wait for a specific selector to appear."""
        try:
            if self.browser_session:
                page = self.browser_session.pages[0] if self.browser_session.pages else None
                if page:
                    page.wait_for_selector(selector, timeout=self.timeout * 1000)
                    return True
        except Exception as e:
            print(f"Wait for selector error: {e}")
        return False
    
    def _sanitize_content(self, html_content: str) -> Dict[str, Any]:
        """
        Phase 2: Content sanitizer - strip dangerous elements and detect injections.
        Returns dict with clean_html, is_safe, warnings.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        warnings = []
        
        # Remove dangerous elements
        for tag in soup.find_all(['script', 'iframe', 'object', 'embed', 'applet']):
            tag.decompose()
        
        # Remove event handlers (onclick, onload, etc.)
        for tag in soup.find_all(True):
            attrs_to_remove = [attr for attr in tag.attrs if attr.startswith('on')]
            for attr in attrs_to_remove:
                del tag[attr]
        
        # Detect common prompt injection patterns
        injection_patterns = [
            r'ignore\s+previous\s+instructions',
            r'disable\s+safety\s+filters',
            r'system\s+prompt',
            r'<thinking>',
            r'\[INSTRUCTIONS\]',
        ]
        
        text_content = soup.get_text() if soup else ""
        for pattern in injection_patterns:
            if re.search(pattern, text_content, re.IGNORECASE):
                warnings.append(f"Potential injection pattern detected: {pattern}")
        
        # Convert back to HTML string
        clean_html = str(soup)
        
        return {
            "clean_html": clean_html,
            "is_safe": len(warnings) == 0,
            "warnings": warnings
        }
    
    def _extract_text(self, html_content: str) -> tuple:
        """
        Phase 3: Document query - extract clean text from HTML.
        Returns (text_content, title) tuple.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract title
        title = ""
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text().strip()
        
        # Remove navigation, headers, footers for cleaner extraction
        for tag in soup.find_all(['nav', 'header', 'footer', 'aside']):
            tag.decompose()
        
        # Extract main content
        text_parts = []
        
        # Try to find main article content first
        main_tag = soup.find('main') or soup.find('article') or soup.find('body')
        if main_tag:
            for p in main_tag.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'li', 'td']):
                text = p.get_text().strip()
                if text:
                    text_parts.append(text)
        else:
            # Fallback to body
            for p in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'li', 'td']):
                text = p.get_text().strip()
                if text:
                    text_parts.append(text)
        
        # Join with newlines
        text_content = '\n\n'.join(text_parts)
        
        return text_content, title
    
    def close(self):
        """Close browser session if open."""
        if self.browser_session:
            try:
                self.browser_session.close()
            except:
                pass
            self.browser_session = None


# Convenience function for quick usage
def extract_web_content(
    url: str,
    timeout: int = 30,
    **kwargs
) -> Dict[str, Any]:
    """
    Quick function to extract content from a URL.
    
    Args:
        url: Target URL
        timeout: Request timeout in seconds
        **kwargs: Additional arguments passed to WebResearchMacro.extract()
        
    Returns:
        Extraction result dictionary
    """
    researcher = WebResearchMacro(timeout=timeout)
    try:
        return researcher.extract(url, **kwargs)
    finally:
        researcher.close()
