"""
Browser Proxy using mitmproxy.

Intercepts browser requests to monitor user browsing activity.
"""

import re
import time
import asyncio
import threading
from typing import Callable, List, Optional
from urllib.parse import urlparse

try:
    import mitmproxy
    from mitmproxy import options
    from mitmproxy.tools import dump
    MITMPROXY_AVAILABLE = True
except ImportError:
    MITMPROXY_AVAILABLE = False


class RequestListener:
    """mitmproxy addon to listen for requests."""

    def __init__(self, callback_func: Callable[[str], None]):
        self.callback_func = callback_func

    def request(self, flow):
        """Called for each HTTP request."""
        if MITMPROXY_AVAILABLE:
            self.callback_func(flow.request.pretty_url)


class BrowserProxy:
    """
    HTTP proxy for monitoring browser traffic.

    Uses mitmproxy to intercept requests and notify about page changes.
    """

    # Extensions to ignore (static assets)
    EXCLUDED_EXTENSIONS = [
        'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'ico',
        'css', 'js', 'ts',
        'mp4', 'webm', 'avi', 'mov', 'm3u8',
        'mp3', 'wav', 'ogg',
        'woff', 'woff2', 'ttf', 'eot',
        'json', 'xml', 'txt', 'pdf',
        'map', 'chain'
    ]

    # Domains to ignore
    EXCLUDED_DOMAINS = [
        'firefox.settings.services.mozilla.com',
        'cdn.mozilla.net',
        'gstatic.com',
        'googleapis.com',
        'google-analytics.com',
        'googletagmanager.com',
        'doubleclick.net',
        'facebook.com',
        'twitter.com',
    ]

    # Minimum interval between callbacks for same-ish URLs
    CALLBACK_INTERVAL = 5.0

    def __init__(
        self,
        callback_func: Callable[[str], None],
        host: str = 'localhost',
        port: int = 8080
    ):
        if not MITMPROXY_AVAILABLE:
            raise ImportError(
                "mitmproxy not installed. Install with: pip install mitmproxy"
            )

        self.callback_func = callback_func
        self.host = host
        self.port = port

        self._listener = RequestListener(self._on_request)
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._last_callback_time = 0.0
        self._last_callback_url = ''

    def _should_exclude(self, url: str) -> bool:
        """Check if URL should be excluded from callbacks."""
        try:
            parsed = urlparse(url)

            # Check domain exclusions
            for domain in self.EXCLUDED_DOMAINS:
                if domain in parsed.netloc:
                    return True

            # Check extension exclusions
            path = parsed.path.lower()
            for ext in self.EXCLUDED_EXTENSIONS:
                if path.endswith(f'.{ext}'):
                    return True

            # Exclude URLs with query strings (usually API calls)
            if parsed.query:
                return True

            return False

        except Exception:
            return True

    def _on_request(self, url: str):
        """Handle intercepted request."""
        try:
            current_time = time.time()

            # Skip excluded URLs
            if self._should_exclude(url):
                return

            # Rate limit callbacks
            time_since_last = current_time - self._last_callback_time
            if time_since_last < self.CALLBACK_INTERVAL:
                return

            # Skip if same URL
            if url == self._last_callback_url:
                return

            self._last_callback_time = current_time
            self._last_callback_url = url
            self.callback_func(url)

        except Exception as e:
            print(f"Proxy callback error: {e}")

    async def _start_proxy(self):
        """Start the mitmproxy server."""
        opts = options.Options(
            listen_host=self.host,
            listen_port=self.port
        )
        master = dump.DumpMaster(
            opts,
            with_termlog=False,
            with_dumper=False,
        )
        master.addons.add(self._listener)

        await master.run()

    async def _shutdown(self):
        """Shutdown the proxy gracefully."""
        tasks = [t for t in asyncio.all_tasks(self._loop) if not t.done()]
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        self._loop.stop()

    def _run_loop(self):
        """Run the async event loop in thread."""
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._start_proxy())

    def start(self):
        """Start the proxy server."""
        if self._running:
            return

        self._running = True
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the proxy server."""
        if not self._running:
            return

        self._running = False

        if self._loop:
            asyncio.run_coroutine_threadsafe(
                self._shutdown(),
                self._loop
            ).result(timeout=5.0)

        if self._thread:
            self._thread.join(timeout=2.0)

    def is_running(self) -> bool:
        """Check if proxy is running."""
        return self._running

    def add_excluded_domain(self, domain: str):
        """Add a domain to exclusion list."""
        if domain not in self.EXCLUDED_DOMAINS:
            self.EXCLUDED_DOMAINS.append(domain)

    def add_excluded_extension(self, ext: str):
        """Add an extension to exclusion list."""
        ext = ext.lstrip('.')
        if ext not in self.EXCLUDED_EXTENSIONS:
            self.EXCLUDED_EXTENSIONS.append(ext)
