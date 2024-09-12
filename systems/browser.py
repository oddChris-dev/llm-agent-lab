from urllib.parse import urlparse
import queue
import time
import threading
import urllib.parse
from urllib.parse import urlparse

from selenium.webdriver import FirefoxProfile
from selenium import webdriver

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions

from systems.browser_proxy import BrowserProxy
from systems.system_base import SystemBase
from utils.html_tools import HtmlTools


class BrowserSystem(SystemBase):
    def __init__(self, app, auto_play=True):
        super().__init__(app)

        self.current_user_session_id = None

        self.search_page = "https://www.google.com/search"
        self.proxy_host = "localhost"
        self.proxy_port = 8080

        self.page_load_func = None
        self.proxy = None
        self.search_browser = None
        self.display_browser = None
        self.user_browser = None

        self.browser_watch_queue = queue.Queue()
        self.user_browser_lock = threading.Lock()
        self.display_browser_lock = threading.Lock()
        self.search_browser_lock = threading.Lock()
        self.browser_monitor = threading.Thread(target=self.watch_browser)

        self.fetching = False
        self.running = False
        self.paused = False
        self.auto_play = auto_play

    def start_user_browser(self, session_id, page_load_callback):
        self.get_user_browser()
        self.current_user_session_id = session_id
        self.page_load_func = page_load_callback

    def get_user_browser(self):
        if not self.user_browser:
            self.proxy = BrowserProxy(self.proxy_request_callback, self.proxy_host, self.proxy_port)
            self.proxy.start()

            self.running = True
            self.browser_monitor.start()

            self.user_browser = webdriver.Firefox(options=self.browser_options(use_proxy=True))
            self.user_browser.set_window_position(2000, 0)

        return self.user_browser

    def get_search_browser(self):
        if not self.search_browser:
            self.search_browser = webdriver.Firefox(options=self.browser_options(use_proxy=False))
            self.search_browser.set_window_position(16, 0)

        return self.search_browser

    def get_display_browser(self):
        if not self.display_browser:
            self.display_browser = webdriver.Firefox(options=self.browser_options(use_proxy=False))
            self.display_browser.set_window_position(603, 0)

        return self.display_browser

    def browser_options(self, use_proxy=True):
        profile = FirefoxProfile()

        # use the browser proxy
        if use_proxy:
            profile.set_preference("network.proxy.type", 1)  # 1 = Manual proxy configuration
            profile.set_preference("network.proxy.http", self.proxy_host)
            profile.set_preference("network.proxy.http_port", self.proxy_port)
            profile.set_preference("network.proxy.ssl", self.proxy_host)
            profile.set_preference("network.proxy.ssl_port", self.proxy_port)
            profile.set_preference("network.proxy.no_proxies_on", "")

        profile.set_preference("http.response.timeout", 5)
        profile.set_preference("dom.max_script_run_time", 5)

        # dark mode
        profile.set_preference("ui.systemUsesDarkTheme", 1)  # 1 for dark mode, 0 for light mode

        firefox_options = webdriver.FirefoxOptions()

        # private mode
        firefox_options.add_argument("-private-window")
        firefox_options.profile = profile

        return firefox_options

    def auto_play_video(self, browser):

        if self.auto_play and "<video" in browser.page_source:
            try:
                video_element = WebDriverWait(browser, 10).until(
                    expected_conditions.presence_of_element_located((By.TAG_NAME, 'video'))
                )
                print("auto_play_video found video element")

                browser.execute_script("arguments[0].play();", video_element)
                print("auto_play_video played video element")

                # Click the Play button
                play_button = WebDriverWait(browser, 10).until(
                    expected_conditions.presence_of_element_located((By.XPATH, '//img[@title="Play"]'))
                )
                play_button.click()
            except Exception as ex:
                print(f"auto_play_video exception {ex}")
            pass

    def get_page_details(self, session_id, browser, page):

        p = urlparse(page.url)
        url_prefix = f"{p.scheme}://{p.netloc}"

        try:
            page.title = HtmlTools.strip_string(browser.title)
            page.body = HtmlTools.get_page_content(
                HtmlTools.strip_string(browser.page_source)
            )
            if HtmlTools.has_error(page.body):
                page.body = ""

            links = HtmlTools.get_page_links(browser.page_source)

            # get up to max_links and mark them as seen
            for link in links:
                href = link["href"]

                if href and href.startswith("/"):
                    href = f"{url_prefix}{href}"

                if HtmlTools.is_url(href):
                    link_page = self.get_session_page(session_id, href)
                    if not link_page.title:
                        link_page.title = link["text"]
                        link_page.set_parent_url(page.url)
                        link_page.save()

        except Exception as ex:
            print(f"get_page_details Exception: {ex}")

        page.save()

    def proxy_request_callback(self, url):
        if not self.fetching:
            print(f"browser changed to {url}")
            self.browser_watch_queue.put(url)

    def watch_browser(self):
        while self.running:
            try:
                watch_url = self.browser_watch_queue.get()
                if watch_url and self.page_load_func:
                    # give the page time to load
                    time.sleep(5)
                    # Block a url has been loaded
                    with self.user_browser_lock:
                        url = self.user_browser.current_url
                        if url and url != self.user_browser_string:
                            page = self.get_session_page(self.current_user_session_id, url)
                            page.set_parent_url(self.user_browser_string)
                            if not page.body:
                                self.get_page_details(self.current_user_session_id, self.user_browser, page)
                                self.page_load_func(page)

            except Exception as ex:
                print(f"watch_browser exception: {ex}")
            finally:
                self.browser_watch_queue.task_done()

    def fetch(self, session_id, url):
        page = self.get_session_page(session_id, url)

        # TODO - check last modified and reload a page

        if not page.body:
            print(f"do_fetch {url}")

            with self.search_browser_lock:
                self.fetching = True
                try:
                    search_browser = self.get_search_browser()
                    search_browser.set_page_load_timeout(10)
                    search_browser.get(url)
                    search_browser.implicitly_wait(10)

                    # give the page a few seconds to render
                    time.sleep(3)

                    self.get_page_details(session_id, search_browser, page)
                except Exception as ex:
                    print(f"do_fetch get page details {url} exception {ex}")

                self.fetching = False

        return page

    def search(self, session_id, search, max_results=10, max_url_length=300):
        print(f"search {search}")

        previous_results = self.get_search_results(session_id, search, max_results)
        start = 0

        for result in previous_results:
            if result.search_rank >= start:
                start = result.search_rank + 1

        results = []

        try:
            self.fetching = True

            params = {
                "q": search,
                "ie": "utf-8",
                "oe": "utf-8",
                "start": start,
                "num": max_results,
            }

            url = self.search_page + '?' + urllib.parse.urlencode(params)

            with self.search_browser_lock:
                search_browser = self.get_search_browser()
                search_browser.set_page_load_timeout(10)
                search_browser.get(url)
                search_browser.implicitly_wait(10)

                # give the page a few seconds to render
                time.sleep(3)
                search_rank = start
                for link in search_browser.find_elements("css selector", "div[data-async-context] a"):
                    try:
                        url = link.get_attribute("href")
                        title = HtmlTools.strip_string(link.text.strip())
                        if title and HtmlTools.is_url(url) and len(url) < max_url_length:
                            page = self.get_session_page(session_id, url)

                            if not page.title:
                                page.title = title

                            page.search_term = search
                            page.search_rank = search_rank
                            page.set_parent_url(url)
                            page.save()

                            results.append(page)
                            search_rank += 1
                    except Exception as ex:
                        print(f"search {search} finding links exception {ex}")

        except Exception as ex:
            print(f"search {search} exception {ex}")

        finally:
            self.fetching = False

        print(f"search {search} starting at {start} found {results}")

        return {"search": search, "start": start, "results": results}

    def show(self, url):
        print(f"show {url}")
        browser = self.get_display_browser()
        browser.get(url)
        browser.implicitly_wait(10)

        if self.auto_play:
            self.auto_play_video(browser)

    def clear(self):
        self.browser_watch_queue.queue.clear()

    def stop(self):
        if self.user_browser:
            self.user_browser.quit()
            self.running = False
            self.browser_watch_queue.put(None)
            self.browser_monitor.join()
            self.proxy.stop()
            self.user_browser = None

        if self.display_browser:
            self.display_browser.quit()
            self.display_browser = None

        if self.search_browser:
            self.search_browser.quit()
            self.search_browser = None

