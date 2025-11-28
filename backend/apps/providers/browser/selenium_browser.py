"""
Selenium Browser Provider.

Provides browser automation using Selenium WebDriver with Firefox.
Supports proxy interception for monitoring user browsing.
"""

import os
import re
import time
import asyncio
import threading
import queue
import urllib.parse
from typing import List, Optional, Callable, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver import FirefoxProfile
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from .base import (
    BaseBrowserProvider,
    BrowserPage,
    BrowserAction,
    BrowserActionType,
    SearchResult,
)


class SeleniumBrowserProvider(BaseBrowserProvider):
    """
    Selenium-based browser provider with Firefox.

    Config options:
        headless: Run browser in headless mode (default: False)
        proxy_host: Proxy host for user browser (default: localhost)
        proxy_port: Proxy port for user browser (default: 8080)
        page_load_timeout: Page load timeout in seconds (default: 30)
        implicit_wait: Implicit wait time (default: 10)
        search_engine: Search engine URL (default: Google)
    """

    SEARCH_ENGINES = {
        'google': 'https://www.google.com/search',
        'duckduckgo': 'https://duckduckgo.com/',
        'bing': 'https://www.bing.com/search',
    }

    def __init__(self, config: dict = None):
        super().__init__(config or {})

        self.headless = self.config.get('headless', False)
        self.proxy_host = self.config.get('proxy_host', 'localhost')
        self.proxy_port = self.config.get('proxy_port', 8080)
        self.page_load_timeout = self.config.get('page_load_timeout', 30)
        self.implicit_wait = self.config.get('implicit_wait', 10)
        self.search_engine = self.config.get('search_engine', 'google')

        self._driver: Optional[webdriver.Firefox] = None
        self._user_driver: Optional[webdriver.Firefox] = None
        self._proxy = None
        self._executor = ThreadPoolExecutor(max_workers=2)
        self._lock = threading.Lock()

        # Browser watching
        self._watch_queue: Optional[queue.Queue] = None
        self._watch_thread: Optional[threading.Thread] = None
        self._watch_callback: Optional[Callable] = None
        self._watching = False

    @property
    def name(self) -> str:
        return 'selenium'

    def _get_firefox_options(self, use_proxy: bool = False) -> webdriver.FirefoxOptions:
        """Create Firefox options with appropriate settings."""
        profile = FirefoxProfile()

        if use_proxy:
            profile.set_preference("network.proxy.type", 1)
            profile.set_preference("network.proxy.http", self.proxy_host)
            profile.set_preference("network.proxy.http_port", self.proxy_port)
            profile.set_preference("network.proxy.ssl", self.proxy_host)
            profile.set_preference("network.proxy.ssl_port", self.proxy_port)
            profile.set_preference("network.proxy.no_proxies_on", "")

        # Performance settings
        profile.set_preference("http.response.timeout", 10)
        profile.set_preference("dom.max_script_run_time", 10)

        # Dark mode
        profile.set_preference("ui.systemUsesDarkTheme", 1)

        # Disable images for faster loading (optional)
        if self.config.get('disable_images', False):
            profile.set_preference("permissions.default.image", 2)

        options = webdriver.FirefoxOptions()
        options.profile = profile

        if self.headless:
            options.add_argument("-headless")

        # Private browsing
        options.add_argument("-private-window")

        return options

    def _ensure_driver(self) -> webdriver.Firefox:
        """Ensure main driver is initialized."""
        if self._driver is None:
            options = self._get_firefox_options(use_proxy=False)
            self._driver = webdriver.Firefox(options=options)
            self._driver.set_page_load_timeout(self.page_load_timeout)
            self._driver.implicitly_wait(self.implicit_wait)

        return self._driver

    def _ensure_user_driver(self) -> webdriver.Firefox:
        """Ensure user browser driver is initialized with proxy."""
        if self._user_driver is None:
            # Start proxy if not running
            if self._proxy is None:
                self._start_proxy()

            options = self._get_firefox_options(use_proxy=True)
            self._user_driver = webdriver.Firefox(options=options)
            self._user_driver.set_page_load_timeout(self.page_load_timeout)
            self._user_driver.implicitly_wait(self.implicit_wait)

        return self._user_driver

    def _start_proxy(self):
        """Start mitmproxy for user browser monitoring."""
        try:
            from .proxy import BrowserProxy
            self._proxy = BrowserProxy(
                callback_func=self._on_proxy_request,
                host=self.proxy_host,
                port=self.proxy_port
            )
            self._proxy.start()
        except ImportError:
            pass  # Proxy support optional

    def _on_proxy_request(self, url: str):
        """Handle proxy request callback."""
        if self._watch_queue and not self._watch_queue.full():
            self._watch_queue.put(url)

    def fetch(
        self,
        url: str,
        wait_time: float = 3.0,
        extract_links: bool = True
    ) -> BrowserPage:
        """Fetch a web page synchronously."""
        with self._lock:
            driver = self._ensure_driver()

            try:
                driver.get(url)
                time.sleep(wait_time)

                html = driver.page_source
                title = driver.title or ''

                # Extract text content
                body = self.extract_text(html)

                # Extract links
                links = []
                if extract_links:
                    links = self._extract_links_selenium(driver, url)

                return BrowserPage(
                    url=url,
                    title=title,
                    body=body,
                    html=html,
                    links=links
                )

            except TimeoutException:
                return BrowserPage(url=url, title='Timeout', body='')
            except WebDriverException as e:
                return BrowserPage(url=url, title='Error', body=str(e))

    async def fetch_async(
        self,
        url: str,
        wait_time: float = 3.0,
        extract_links: bool = True
    ) -> BrowserPage:
        """Fetch a web page asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            partial(self.fetch, url, wait_time, extract_links)
        )

    def _extract_links_selenium(
        self,
        driver: webdriver.Firefox,
        base_url: str
    ) -> List[Dict[str, str]]:
        """Extract links using Selenium."""
        links = []
        try:
            elements = driver.find_elements(By.TAG_NAME, 'a')
            parsed_base = urlparse(base_url)
            base_prefix = f"{parsed_base.scheme}://{parsed_base.netloc}"

            for elem in elements[:100]:  # Limit to first 100 links
                try:
                    href = elem.get_attribute('href')
                    text = elem.text.strip()

                    if href:
                        # Make relative URLs absolute
                        if href.startswith('/'):
                            href = f"{base_prefix}{href}"

                        if self.is_valid_url(href):
                            links.append({'href': href, 'text': text})
                except Exception:
                    continue

        except Exception:
            pass

        return links

    def search(
        self,
        query: str,
        max_results: int = 10,
        start: int = 0
    ) -> List[SearchResult]:
        """Perform a Google search."""
        with self._lock:
            driver = self._ensure_driver()

            search_url = self.SEARCH_ENGINES.get(
                self.search_engine,
                self.SEARCH_ENGINES['google']
            )

            params = {
                'q': query,
                'start': start,
                'num': max_results,
            }
            url = f"{search_url}?{urllib.parse.urlencode(params)}"

            results = []

            try:
                driver.get(url)
                time.sleep(3)  # Wait for results to load

                # Find search result elements (Google-specific)
                if self.search_engine == 'google':
                    result_elements = driver.find_elements(
                        By.CSS_SELECTOR,
                        "div[data-async-context] a"
                    )
                else:
                    result_elements = driver.find_elements(By.TAG_NAME, 'a')

                rank = start
                for elem in result_elements:
                    try:
                        href = elem.get_attribute('href')
                        title = elem.text.strip()

                        if (title and href and
                            self.is_valid_url(href) and
                            len(href) < 300):

                            results.append(SearchResult(
                                url=href,
                                title=title,
                                rank=rank
                            ))
                            rank += 1

                            if len(results) >= max_results:
                                break
                    except Exception:
                        continue

            except Exception as e:
                print(f"Search error: {e}")

            return results

    async def search_async(
        self,
        query: str,
        max_results: int = 10,
        start: int = 0
    ) -> List[SearchResult]:
        """Perform search asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            partial(self.search, query, max_results, start)
        )

    def execute_action(self, action: BrowserAction) -> bool:
        """Execute a browser action."""
        driver = self._ensure_driver()

        try:
            if action.action_type == BrowserActionType.NAVIGATE:
                driver.get(action.value)
                return True

            elif action.action_type == BrowserActionType.CLICK:
                elem = WebDriverWait(driver, action.timeout).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, action.selector))
                )
                elem.click()
                return True

            elif action.action_type == BrowserActionType.TYPE:
                elem = WebDriverWait(driver, action.timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, action.selector))
                )
                elem.clear()
                elem.send_keys(action.value)
                return True

            elif action.action_type == BrowserActionType.SCROLL:
                driver.execute_script(f"window.scrollBy(0, {action.value or 500});")
                return True

            elif action.action_type == BrowserActionType.WAIT:
                time.sleep(float(action.value or action.timeout))
                return True

            elif action.action_type == BrowserActionType.EXECUTE_JS:
                driver.execute_script(action.value)
                return True

            elif action.action_type == BrowserActionType.SCREENSHOT:
                # Screenshot handled separately
                return True

        except Exception as e:
            print(f"Action error: {e}")
            return False

        return False

    def screenshot(self, full_page: bool = False) -> bytes:
        """Take a screenshot."""
        driver = self._ensure_driver()

        if full_page:
            # Get full page height
            total_height = driver.execute_script(
                "return document.body.scrollHeight"
            )
            driver.set_window_size(1920, total_height)

        return driver.get_screenshot_as_png()

    def navigate(self, url: str) -> bool:
        """Navigate to a URL."""
        try:
            driver = self._ensure_driver()
            driver.get(url)
            return True
        except Exception:
            return False

    def get_current_url(self) -> str:
        """Get current URL."""
        driver = self._ensure_driver()
        return driver.current_url

    def get_page_source(self) -> str:
        """Get page source HTML."""
        driver = self._ensure_driver()
        return driver.page_source

    def start_watching(
        self,
        callback: Callable[[str], None],
        session_id: Optional[str] = None
    ):
        """Start watching user browser navigation."""
        if self._watching:
            return

        self._watch_callback = callback
        self._watch_queue = queue.Queue(maxsize=100)
        self._watching = True

        # Ensure user driver with proxy is running
        self._ensure_user_driver()

        # Start watch thread
        self._watch_thread = threading.Thread(target=self._watch_loop)
        self._watch_thread.daemon = True
        self._watch_thread.start()

    def _watch_loop(self):
        """Watch for browser navigation changes."""
        while self._watching:
            try:
                url = self._watch_queue.get(timeout=1.0)
                if url and self._watch_callback:
                    # Wait for page to load
                    time.sleep(2)
                    self._watch_callback(url)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Watch error: {e}")

    def stop_watching(self):
        """Stop watching browser navigation."""
        self._watching = False
        if self._watch_thread:
            self._watch_thread.join(timeout=2.0)

    def health_check(self) -> bool:
        """Check if Selenium/Firefox is available."""
        try:
            from selenium import webdriver
            # Check if geckodriver is available
            options = webdriver.FirefoxOptions()
            options.add_argument("-headless")
            driver = webdriver.Firefox(options=options)
            driver.quit()
            return True
        except Exception:
            return False

    def close(self):
        """Close all browser instances and cleanup."""
        if self._driver:
            try:
                self._driver.quit()
            except Exception:
                pass
            self._driver = None

        if self._user_driver:
            try:
                self._user_driver.quit()
            except Exception:
                pass
            self._user_driver = None

        if self._proxy:
            try:
                self._proxy.stop()
            except Exception:
                pass
            self._proxy = None

        self._watching = False
        self._executor.shutdown(wait=False)

    def auto_play_video(self):
        """Try to auto-play video on current page."""
        driver = self._ensure_driver()

        if "<video" not in driver.page_source:
            return False

        try:
            video = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.TAG_NAME, 'video'))
            )
            driver.execute_script("arguments[0].play();", video)
            return True
        except Exception:
            return False

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
