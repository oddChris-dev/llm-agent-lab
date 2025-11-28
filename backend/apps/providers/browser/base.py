"""
Base Browser Provider interface.

All browser providers implement this interface for web automation.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from enum import Enum


class BrowserActionType(str, Enum):
    """Types of browser actions."""
    NAVIGATE = 'navigate'
    CLICK = 'click'
    TYPE = 'type'
    SCROLL = 'scroll'
    SCREENSHOT = 'screenshot'
    WAIT = 'wait'
    EXECUTE_JS = 'execute_js'


@dataclass
class BrowserAction:
    """A browser action to perform."""
    action_type: BrowserActionType
    selector: Optional[str] = None
    value: Optional[str] = None
    timeout: float = 10.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'action_type': self.action_type.value,
            'selector': self.selector,
            'value': self.value,
            'timeout': self.timeout,
        }


@dataclass
class BrowserPage:
    """Represents a fetched web page."""
    url: str
    title: str = ''
    body: str = ''
    html: str = ''
    links: List[Dict[str, str]] = field(default_factory=list)
    screenshot: Optional[bytes] = None
    fetched_at: datetime = field(default_factory=datetime.utcnow)

    # For search results
    search_term: Optional[str] = None
    search_rank: Optional[int] = None
    parent_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'url': self.url,
            'title': self.title,
            'body': self.body,
            'links': self.links,
            'fetched_at': self.fetched_at.isoformat(),
            'search_term': self.search_term,
            'search_rank': self.search_rank,
        }


@dataclass
class SearchResult:
    """A search result item."""
    url: str
    title: str
    snippet: str = ''
    rank: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'url': self.url,
            'title': self.title,
            'snippet': self.snippet,
            'rank': self.rank,
        }


class BaseBrowserProvider(ABC):
    """
    Abstract base class for browser providers.

    Implementations must provide:
    - fetch(): Fetch a web page
    - search(): Perform web search
    - execute_action(): Execute browser action
    - screenshot(): Take screenshot
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize provider with configuration.

        Args:
            config: Provider-specific configuration dict
        """
        self.config = config

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (e.g., 'selenium', 'playwright')."""
        pass

    @abstractmethod
    def fetch(
        self,
        url: str,
        wait_time: float = 3.0,
        extract_links: bool = True
    ) -> BrowserPage:
        """
        Fetch a web page and extract content.

        Args:
            url: URL to fetch
            wait_time: Time to wait for page to render
            extract_links: Whether to extract page links

        Returns:
            BrowserPage with content
        """
        pass

    @abstractmethod
    async def fetch_async(
        self,
        url: str,
        wait_time: float = 3.0,
        extract_links: bool = True
    ) -> BrowserPage:
        """Fetch a web page asynchronously."""
        pass

    @abstractmethod
    def search(
        self,
        query: str,
        max_results: int = 10,
        start: int = 0
    ) -> List[SearchResult]:
        """
        Perform a web search.

        Args:
            query: Search query
            max_results: Maximum number of results
            start: Starting position for pagination

        Returns:
            List of SearchResult objects
        """
        pass

    @abstractmethod
    async def search_async(
        self,
        query: str,
        max_results: int = 10,
        start: int = 0
    ) -> List[SearchResult]:
        """Perform a web search asynchronously."""
        pass

    @abstractmethod
    def execute_action(self, action: BrowserAction) -> bool:
        """
        Execute a browser action.

        Args:
            action: BrowserAction to execute

        Returns:
            True if action was successful
        """
        pass

    @abstractmethod
    def screenshot(self, full_page: bool = False) -> bytes:
        """
        Take a screenshot of the current page.

        Args:
            full_page: Capture full page or visible viewport

        Returns:
            Screenshot as PNG bytes
        """
        pass

    @abstractmethod
    def navigate(self, url: str) -> bool:
        """Navigate to a URL."""
        pass

    @abstractmethod
    def get_current_url(self) -> str:
        """Get the current page URL."""
        pass

    @abstractmethod
    def get_page_source(self) -> str:
        """Get the current page HTML source."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check if browser is available."""
        pass

    @abstractmethod
    def close(self):
        """Close the browser and cleanup resources."""
        pass

    def start_watching(
        self,
        callback: Callable[[str], None],
        session_id: Optional[str] = None
    ):
        """
        Start watching browser navigation for the user browser.

        Override in providers that support browser watching.

        Args:
            callback: Function to call when page changes
            session_id: Optional session identifier
        """
        raise NotImplementedError(
            f"{self.name} provider does not support browser watching"
        )

    def stop_watching(self):
        """Stop watching browser navigation."""
        pass

    def extract_text(self, html: str) -> str:
        """Extract readable text from HTML."""
        import re
        from html import unescape

        # Remove scripts and styles
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)

        # Decode HTML entities
        text = unescape(text)

        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def extract_links(self, html: str, base_url: str = '') -> List[Dict[str, str]]:
        """Extract links from HTML."""
        import re
        from urllib.parse import urljoin

        links = []
        pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]*)</a>'

        for match in re.finditer(pattern, html, re.IGNORECASE):
            href = match.group(1)
            text = match.group(2).strip()

            # Make URL absolute
            if base_url and not href.startswith(('http://', 'https://')):
                href = urljoin(base_url, href)

            if href.startswith(('http://', 'https://')):
                links.append({'href': href, 'text': text})

        return links

    def is_valid_url(self, url: str) -> bool:
        """Check if URL is valid."""
        from urllib.parse import urlparse
        try:
            result = urlparse(url)
            return all([result.scheme in ('http', 'https'), result.netloc])
        except Exception:
            return False
