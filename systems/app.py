import threading

from systems.config import Config
from systems.database import Database

from systems.text_generator import TextGenerator
from systems.browser import BrowserSystem
from systems.game_system import GameSystem
from systems.speach_listener import SpeachListener
from systems.text_to_speach import TextToSpeach
from systems.media_player import MediaPlayer
from systems.transcript_player import TranscriptPlayer


class App:
    instance = None

    def __init__(self):
        App.instance = self

        self.cuda_lock = threading.Lock()
        self.browser_system = None
        self.text_generator_system = None
        self.listen_system = None
        self.media_player_system = None
        self.speech_system = None
        self.game_system = None
        self.transcript_player = None
        self.config_system = None
        self.db_system = None

        if self.config().auto_play_media:
            self.media_player().start()

    def media_player(self):

        if not self.media_player_system:
            self.media_player_system = MediaPlayer(self.config().playlist_path, self.config().vlc_player_path)

        return self.media_player_system

    def db(self):
        if not self.db_system:
            self.db_system = Database()
            self.db_system.connect()

        return self.db_system

    def config(self):
        if not self.config_system:
            self.config_system = Config()

        return self.config_system

    def browser(self):

        if not self.browser_system:
            self.browser_system = BrowserSystem(self, auto_play=True)

        return self.browser_system

    def text_generator(self):

        if not self.text_generator_system:
            self.text_generator_system = TextGenerator(
                model_path=self.config().ai_model_path,
                max_tokens=512,
                cuda_lock=self.cuda_lock
            )
            self.text_generator_system.load_model()

        return self.text_generator_system

    def game(self):

        if not self.game_system:
            self.game_system = GameSystem(self)

        return self.game_system

    def transcripts(self):

        if not self.transcript_player:
            self.transcript_player = TranscriptPlayer(self)

        return self.transcript_player

    def speech(self):

        if not self.speech_system:
            self.speech_system = TextToSpeach(
                self,
                model_path=self.config().text_to_speech_model_path,
                tmp_path=self.config().audio_temp_path,
                default_voice=self.config().default_voice,
                cuda_lock=self.cuda_lock
            )

        return self.speech_system

    def listener(self):

        if not self.listen_system:
            self.listen_system = SpeachListener(model_path=self.config().speech_to_text_model_path)

        return self.listen_system

    def stop(self):
        if self.game_system:
            self.game_system.stop()

        if self.browser_system:
            self.browser_system.stop()

        if self.speech_system:
            self.speech_system.stop()

        if self.listen_system:
            self.listen_system.stop()

        if self.media_player_system:
            self.media_player_system.stop()

        if self.transcript_player:
            self.transcript_player.stop()

        if self.db_system:
            self.db_system.close()
