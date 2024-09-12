
import unittest

from systems.database import Database
from utils.html_tools import HtmlTools


class TestHtmlTools(unittest.TestCase):

    def test_strip_string(self):
        self.assertEqual(HtmlTools.strip_string("stepladder"), "ladder")
        self.assertEqual(HtmlTools.strip_string("NASA https://en.wikipedia.org/wiki/List_of_NASA_robots Robots"), "NASA Robots")

if __name__ == '__main__':
    unittest.main()