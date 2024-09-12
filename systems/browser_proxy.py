import time
import re
import threading
import asyncio
import mitmproxy
from mitmproxy import options
from mitmproxy.tools import dump
from urllib.parse import urlparse


class RequestListener:
    def __init__(self, callback_func):
        self.callback_func = callback_func

    def request(self, flow: mitmproxy.http.HTTPFlow):
        self.callback_func(flow.request.pretty_url)


class BrowserProxy:
    def __init__(self, callback_func, host, port):
        self.host = host
        self.port = port
        self.callback_func = callback_func
        self.listener = RequestListener(self.callback_wrapper)
        self.loop = asyncio.new_event_loop()
        self.proxy_thread = threading.Thread(target=self.run_proxy)
        self.running = False

        self.LOG_INTERVAL = 5
        self.last_logged_time = 0
        self.EXCLUDED_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif', 'ts', 'js', 'mp4', 'avi', 'mov', 'webp', 'css', 'ico',
                                    'json', 'svg', 'm3u8', 'webm', 'txt', 'pdf', 'chain']
        self.EXCLUDED_DOMAINS = [
            'firefox.settings.services.mozilla.com',
            'cdn.mozilla.net'
            'gstatic.com'
        ]

    def should_exclude(self, url):
        try:
            # Regex pattern to match excluded domains
            domains_pattern = r'(' + '|'.join(re.escape(domain) for domain in self.EXCLUDED_DOMAINS) + r')'

            # Check if URL matches excluded domains pattern
            if re.search(domains_pattern, url, re.IGNORECASE):
                return True

            # Regex pattern to match file extensions with a preceding period (.)
            extensions_pattern = r'\.(' + '|'.join(self.EXCLUDED_EXTENSIONS) + r')($|\?)'

            # Check if URL matches file extensions pattern
            if re.search(extensions_pattern, url, re.IGNORECASE):
                return True

            # Exclude if it has an excluded extension and a query string
            has_query_string = bool(urlparse(url).query)
            return has_query_string
        except Exception as ex:
            print(f"should_exclude exception {ex}")

        return False

    def callback_wrapper(self, url):
        try:
            current_time = time.time()
            if not self.should_exclude(url) and current_time - self.last_logged_time >= self.LOG_INTERVAL:
                self.last_logged_time = current_time
                self.callback_func(url)
        except Exception as ex:
            print(f"browser proxy callback_wrapper exception {ex}")

    async def start_proxy(self, host, port):
        print("starting proxy")
        opts = options.Options(listen_host=host, listen_port=port)
        master = dump.DumpMaster(
            opts,
            with_termlog=False,
            with_dumper=False,
        )
        master.addons.add(self.listener)

        await master.run()

        return master

    async def shutdown_proxy(self):
        """Gracefully shut down the asyncio loop."""
        tasks = [t for t in asyncio.all_tasks(self.loop) if not t.done()]
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        self.loop.stop()

    def run_proxy(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.start_proxy(self.host, self.port))

    def stop(self):
        self.running = False
        asyncio.run_coroutine_threadsafe(self.shutdown_proxy(), self.loop).result()
        self.proxy_thread.join()

    def start(self):
        self.running = True
        self.proxy_thread.start()
