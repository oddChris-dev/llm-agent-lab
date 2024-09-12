from flask import redirect, url_for, Blueprint

from pages.base_page import BasePage


class MediaPage(BasePage):
    def __init__(self, app):
        super().__init__(app)
        self.blueprint = Blueprint('media_page', __name__, template_folder='templates')
        self.routes()

    def routes(self):

        @self.blueprint.route('/music/back', methods=['POST'])
        def previous_song():
            self.app.media_player().previous_media()
            return redirect(url_for('index_page.index'))

        @self.blueprint.route('/music/next', methods=['POST'])
        def skip_song():
            self.app.media_player().next_media()
            return redirect(url_for('index_page.index'))

        # Route to reload prompts
        @self.blueprint.route('/music/start', methods=['POST'])
        def media_start():
            self.app.media_player().start()
            return redirect(url_for('index_page.index'))

        @self.blueprint.route('/music/stop', methods=['POST'])
        def media_stop():
            self.app.media_player().stop()
            return redirect(url_for('index_page.index'))

