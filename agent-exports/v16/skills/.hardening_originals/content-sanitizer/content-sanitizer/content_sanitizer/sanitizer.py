import re
import html
from dataclasses import dataclass
from typing import List, Optional
import urllib.parse

@dataclass
class SanitizationResult:
    """Result of content sanitization with safety metadata."""
    clean_text: str
    dangerous_elements_removed: int = 0
    instruction_patterns_detected: List[str] = None

    def __post_init__(self):
        if self.instruction_patterns_detected is None:
            self.instruction_patterns_detected = []

    def is_safe(self) -> bool:
        """Returns True if no dangerous patterns detected."""
        return len(self.instruction_patterns_detected) == 0


class ContentSanitizer:
    """Insulating layer for web content - protects against prompt injection."""

    # Patterns that indicate potential instruction injection
    INSTRUCTION_PATTERNS = [
        (r"ignore\s+all\s+previous\s+instructions", "Ignore previous instructions"),
        (r"system\s+prompt", "System prompt reference"),
        (r"you\s+must\s+output", "Forced output command"),
        (r"remember\s+this\s+rule", "Rule injection attempt"),
        (r"from\s+now\s+on", "Behavior modification"),
        (r"override\s+instructions", "Instruction override"),
        (r"secret\s+instruction", "Secret instruction"),
        (r"hidden\s+command", "Hidden command"),
    ]

    @staticmethod
    def clean(content: str) -> SanitizationResult:
        """
        Sanitize raw HTML/text content.

        Args:
            content: Raw HTML or text to sanitize

        Returns:
            SanitizationResult with clean text and safety metadata
        """
        if not content:
            return SanitizationResult(clean_text="")

        dangerous_count = 0
        patterns_found = []

        # Decode HTML entities first
        try:
            content = html.unescape(content)
        except:
            pass

        # Remove script tags and content
        before_len = len(content)
        content = re.sub(r"<script[^>]*>[\s\S]*?</script>", "", content, flags=re.IGNORECASE)
        dangerous_count += max(0, (before_len - len(content)) // 10)  # Estimate count

        # Remove iframe tags
        before_len = len(content)
        content = re.sub(r"<iframe[^>]*>[\s\S]*?</iframe>", "", content, flags=re.IGNORECASE)
        dangerous_count += max(0, (before_len - len(content)) // 10)

        # Remove object/embed tags
        for tag in ["object", "embed"]:
            before_len = len(content)
            content = re.sub(rf"<{tag}[^>]*>[\s\S]*?</{tag}>", "", content, flags=re.IGNORECASE)
            dangerous_count += max(0, (before_len - len(content)) // 10)

        # Remove event handlers (onclick, onload, etc.)
        before_len = len(content)
        content = re.sub(r"\s+on\w+=[^<>"]*", "", content, flags=re.IGNORECASE)
        dangerous_count += max(0, (before_len - len(content)) // 15)

        # Remove style attributes with javascript
        before_len = len(content)
        content = re.sub(r"style\s*=\s*[^<>"]*javascript:[^<>"]*", "", content, flags=re.IGNORECASE)
        dangerous_count += max(0, (before_len - len(content)) // 20)

        # Extract text from remaining HTML
        # Remove all remaining tags but preserve text content
        content = re.sub(r"<[^>]+>", "", content)

        # Decode any remaining HTML entities
        try:
            content = html.unescape(content)
        except:
            pass

        # Clean up whitespace
        content = re.sub(r"\s+", " ", content).strip()

        # Check for instruction patterns in the cleaned text
        for pattern, description in ContentSanitizer.INSTRUCTION_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                patterns_found.append(description)

        return SanitizationResult(
            clean_text=content,
            dangerous_elements_removed=dangerous_count,
            instruction_patterns_detected=patterns_found
        )

    @staticmethod
    def fetch_safe(url: str, timeout: int = 10) -> Optional[SanitizationResult]:
        """
        Safely fetch and sanitize content from a URL.

        Args:
            url: URL to fetch
            timeout: Request timeout in seconds

        Returns:
            SanitizationResult or None if fetch fails
        """
        try:
            import urllib.request
            import ssl

            # Create SSL context that doesn't verify (for testing)
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; ContentSanitizer/1.0)",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                }
            )

            with urllib.request.urlopen(request, timeout=timeout, context=ssl_context) as response:
                content = response.read().decode("utf-8", errors="ignore")
                return ContentSanitizer.clean(content)

        except Exception as e:
            # Return a result indicating fetch failure
            return SanitizationResult(
                clean_text=f"[Failed to fetch content: {str(e)}]",
                dangerous_elements_removed=0,
                instruction_patterns_detected=[]
            )
