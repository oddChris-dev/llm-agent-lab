import re
import math
from collections import Counter


class TextTools:
    @staticmethod
    def split_speech(speech_text, max_length=64):
        """
        Splits the response into chunks that are each shorter than max_length.
        This method tries to split on punctuation followed by spaces to maintain contextual coherence,
        filtering out empty lines or segments that consist only of punctuation.
        """
        if not isinstance(speech_text, str):
            print(f"Warning: Expected string, got {type(speech_text)} instead.")
            return []

        pieces = []
        current_piece = ""
        # Iterate over each character and decide where to split
        words = speech_text.split()
        for word in words:
            # Check if adding this word plus a space exceeds max_length
            test_piece = current_piece + ' ' + word if current_piece else word
            if len(test_piece) > max_length:
                # If current piece ends with punctuation, it's a good split point
                if current_piece and current_piece[-1] in "!#$%&'()*+, -./:;<=>?@[\\]^_`{|}~\"":
                    pieces.append(current_piece)
                    current_piece = word
                else:
                    # Find the last punctuation to split at a natural point
                    last_punct = max(current_piece.rfind(','), current_piece.rfind('.'), current_piece.rfind('!'),
                                     current_piece.rfind('?'), current_piece.rfind(';'))
                    if last_punct != -1 and last_punct + 1 != len(current_piece):
                        # Split at the last punctuation if there is any and it's not the last character
                        pieces.append(current_piece[:last_punct + 1])
                        current_piece = current_piece[last_punct + 2:].lstrip() + ' ' + word
                    else:
                        # If no punctuation, split at the last word
                        pieces.append(current_piece)
                        current_piece = word
            else:
                current_piece = test_piece

        if current_piece.strip():
            pieces.append(current_piece.strip())

        return pieces

    @staticmethod
    def separate_acronyms(text):
        # Regular expression to find acronyms (2 to 5 capital letters)
        acronym_pattern = r'\b[A-Z]{2,4}\b'

        # Replace each acronym with dashed version
        return re.sub(acronym_pattern, lambda match: '-'.join(match.group()), text)

    @staticmethod
    def calculate_entropy(text):
        probabilities = [freq / len(text) for freq in Counter(text).values()]
        entropy = -sum(p * math.log2(p) for p in probabilities)
        return entropy

    @staticmethod
    def detect_low_entropy(text, threshold=3.5):
        entropy = TextTools.calculate_entropy(text)
        if entropy < threshold:
            return True
        return False

    @staticmethod
    def detect_repetition(text):
        return TextTools.detect_low_entropy(text, 4.4)