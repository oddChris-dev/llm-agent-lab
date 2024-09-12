import re

from bs4 import BeautifulSoup, Comment


class HtmlTools:
    error_strings = [
        "page not found",
        "page cannot be found",
        "Page unavailable",
        "page is currently unavailable",
        "This video isn't available anymore",
        "Video was deleted",
        "Access denied",
        "can't find that page",
        "there's no page here",
        "the page does not exist",
        "unable to connect",
        "gateway timeout",
        "Internal Server Error",
        "Service Unavailable",
        " 404 ",
        " 403 ",
        "There is currently no text in this page",
        "you have been blocked",
        "requested was not found"
    ]

    url_pattern = r"\bhttps?://[^\s<>\",;:(){}[\]']+"

    strip_patterns = [
        url_pattern,
        r'\.{3,}',
        r'\bstep'
    ]

    @staticmethod
    def is_url(text):
        url = ""
        try:
            for match in re.finditer(HtmlTools.url_pattern, str(text), flags=re.IGNORECASE):
                url = match.group(0)  # Get the first matched URL
        except Exception as ex:
            print(f"is_url({url}) exception {ex}")
        return url

    @staticmethod
    def has_error(text):
        if not text:
            return True

        return any(substring.lower() in text.lower() for substring in HtmlTools.error_strings)

    @staticmethod
    def strip_string(text):
        for pattern in HtmlTools.strip_patterns:
            text = re.sub(pattern, '', text, flags=re.I)
        return HtmlTools.normalize_whitespace(text)

    @staticmethod
    def normalize_whitespace(text):
        return re.sub(r'\s+', ' ', text).strip()

    @staticmethod
    def clean_soup(html_source):
        soup = BeautifulSoup(html_source, "html.parser")

        try:
            # Decompose unwanted elements
            for data in soup(['meta', 'style', 'script', 'header', 'footer', 'nav', 'aside', 'form', 'noscript',
                              'iframe', 'object', 'embed', 'video', 'audio', 'meta']):
                data.decompose()
        except Exception as ex:
            print(f"clean_soup unwanted elements exception {ex}")

        try:
            # Decompose elements by class
            for data in soup.find_all(class_=[
                'ad', 'ads', 'sponsored', 'promo', 'nav', 'mobile-hide', 'navigation',
                'cookie-banner', 'cookie-consent', 'cookie-notice', 'cookie-policy',
                'topbar', 'hidden'
            ]):
                data.decompose()
        except Exception as ex:
            print(f"clean_soup unwanted classes exception {ex}")

        try:
            for data in soup.find_all('div', attrs={'role': 'navigation'}):
                data.decompose()
            # Remove cookie consent banners
            for data in soup.find_all(id=['left-sidebar', 'navigation', 'side-categories', 'site-nav']):
                data.decompose()
        except Exception as ex:
            print(f"clean_soup unwanted navigation exception {ex}")

        try:
            # Remove comments
            for comment in soup.find_all(text=lambda text: isinstance(text, Comment)):
                comment.extract()
            # Remove hidden elements
            for element in soup.find_all(style=lambda value: value and 'display:none' in value):
                element.decompose()
            # Remove inline styles
            for tag in soup.find_all(True):
                del tag['style']
            # Remove empty tags
            for tag in soup.find_all():
                if not tag.contents or not tag.get_text(strip=True):
                    tag.decompose()
        except Exception as ex:
            print(f"clean_soup remove invisible exception {ex}")

        try:
            # Remove copyright notices and legal disclaimers
            for data in soup.find_all(
                    text=lambda
                            t: 'copyright' in t.lower() or '©' in t or 'cookies' in t.lower() or 'website' in t.lower()
            ):
                try:
                    parent = data.find_parent()
                    if parent:
                        parent.decompose()
                    else:
                        data.extract()
                except Exception:
                    data.extract()
        except Exception as ex:
            print(f"clean_soup remove copyright and cookies exception {ex}")

        return soup

    @staticmethod
    def get_page_content(html_source):
        soup = HtmlTools.clean_soup(html_source)

        text = soup.get_text(separator=' ', strip=True)
        # Normalize whitespace
        return HtmlTools.normalize_whitespace(text)

    @staticmethod
    def get_page_links(html_source):
        soup = HtmlTools.clean_soup(html_source)

        links = []

        for data in soup(['a']):
            links.append({
                "text": data.get_text(separator=' ', strip=True),
                "href": data.get('href')
            })

        return links

    @staticmethod
    def get_search_links(search_result_html):
        soup = BeautifulSoup(search_result_html, 'html.parser')
        links = soup.select("div[data-async-context]")

        print(f"search returned {links}")

        return str(links)
