import threading

from systems.game_moves import GameMoves


class GameSystem:
    def __init__(self, app):
        self.app = app

        self.playing = False
        self.running = False
        self.play_thread = None
        self.current_game = None
        self.session = None
        self.last_response = ""

    def start_playing(self, session):
        self.running = True
        self.session = session
        self.last_response = ""
        self.current_game = GameMoves(self.app, session)

        self.play_thread = threading.Thread(target=self.do_play)
        self.play_thread.start()

    def start_user_browser(self):
        if self.running and self.current_game:
            self.app.browser().start_user_browser(self.current_game.session.id, self.on_page_load)

    def start_voice_listener(self):
        self.app.listener().start(self.on_user_input)

    def stop(self):
        self.running = False

        if self.play_thread:
            self.play_thread.join()
            self.play_thread = None

        self.current_game = None

    def on_page_load(self, page):
        if self.running and self.current_game:
            self.current_game.on_page_load(page)

    def on_user_input(self, user_input):
        if self.running and self.current_game:
            self.current_game.on_user_input(user_input)

    def do_play(self):
        response = ""
        while self.running:
            response = self.current_game.next_turn(response)
