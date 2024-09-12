
import unittest

from voice_bot.systems.database import Database
from voice_bot.utils.html_tools import HtmlTools
from voice_bot.utils.text_tools import TextTools


class TestTextTools(unittest.TestCase):

    def test_repetitive(self):
        db = Database()
        db.connect()

        query = ("SELECT content from transcripts;")
        results = db.fetch_results(query)

        # If the page is found, return it
        for row in results:

            text = row[0]
            if TextTools.detect_repetition(text):
                entropy = TextTools.calculate_entropy(text)
                print(f"LOW ENTROPY {entropy}\n {text}")

        db.close()


if __name__ == '__main__':
    unittest.main()